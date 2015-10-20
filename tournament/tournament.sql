-- Table definitions for the tournament project.

-- !!!!WARNING!!!!: This sql file deletes the tournament database and
-- creates a new, blank one!! Make sure you want to do this!

-- Drop the tournament database if it exists, then create it
DROP DATABASE IF EXISTS tournament;
CREATE DATABASE tournament;
\c tournament

-- Create Tables
CREATE TABLE registrants (
    id      serial PRIMARY KEY,
    name      text NOT NULL
);

CREATE TABLE tournaments (
    id      serial PRIMARY KEY,
    name      text NOT NULL
);

CREATE TABLE players (
    id               serial PRIMARY KEY,
    tournament_id   integer NOT NULL REFERENCES tournaments (id) ON DELETE CASCADE,
    registrant_id   integer NOT NULL REFERENCES registrants (id) ON DELETE CASCADE,
    UNIQUE (tournament_id, registrant_id) -- register a player for a tournament only once
);

CREATE TABLE matches (
    id               serial PRIMARY KEY,
    tournament_id   integer NOT NULL REFERENCES tournaments (id) ON DELETE CASCADE,
    winner          integer NOT NULL REFERENCES players (id) ON DELETE CASCADE,
    loser           integer REFERENCES players (id) ON DELETE SET NULL,
    is_tie          boolean DEFAULT FALSE,
    is_bye          boolean DEFAULT FALSE
);

-- Create Indexes
CREATE UNIQUE INDEX one_bye_per_tournament ON matches (tournament_id, winner) WHERE is_bye; -- enforce one bye per tournament rule in DB

-- Create Views
CREATE VIEW player_standings AS
    -- this view generates a list of player standings based on:
    --     o number of wins the player has had
    --     o number of "opponent match wins" (omw) for the player's former opponents
    SELECT
        t.id AS tournament_id,
        p.id AS player_id,
        r.name AS player_name,
        (
            SELECT
                COUNT(id)
            FROM matches
            WHERE winner = p.id OR loser = p.id
        ) AS count_matches, -- display number of matches the player has been in
        (
            SELECT COUNT(id)
            FROM matches
            WHERE winner = p.id AND is_tie = FALSE
        ) AS count_wins, -- display the number of wins for the player
        (
            SELECT SUM(count_wins1) -- add up the wins of the player's former opponents
            FROM
                (
                    SELECT COUNT(p1.id) AS count_wins1
                    FROM
                        players p1,
                        matches m1
                    WHERE m1.winner = p1.id AND m1.is_tie = FALSE AND p1.id IN (
                        SELECT p2.id
                        FROM
                            players p2,
                            matches m1
                        WHERE
                            (
                                p2.id = m1.winner AND m1.loser = p.id AND is_tie = FALSE
                            ) OR (
                                p2.id = m1.loser AND m1.winner = p.id AND is_tie = FALSE
                            )
                    )
                ) AS count_all_wins
        ) AS omw -- display the player's omw score
    FROM
        tournaments t,
        players p,
        registrants r
    WHERE p.registrant_id = r.id AND t.id = p.tournament_id
    ORDER BY
        tournament_id,
        count_wins DESC,
        omw DESC,
        player_id;

CREATE VIEW unmatched_pairs AS
    -- this view generates a list of players in each tournament who have not yet faced each other
    -- the view is called by the function swiss_pairings()
    SELECT
        ps.tournament_id,
        ps.player_id AS player_one_id,
        ps.player_name AS player_one_name,
        player_two.id AS player_two_id,
        player_two.name AS player_two_name,
        ps.count_wins AS player_one_wins,
        ps.omw AS player_one_omw,
        (
            SELECT count(id)
            FROM matches
            WHERE winner = player_two.id AND is_tie = FALSE
        ) AS player_two_wins -- display player two's wins; this will be used as a sorting mechanism
    FROM
        player_standings ps, -- iterate through the player_standings view
        (
            SELECT
                p1.id,
                r1.name
            FROM
                players p1,
                registrants r1
            WHERE p1.registrant_id = r1.id
        ) AS player_two -- for each player in player_standings, add a row to the results for another player who has not yet faced player_one
    WHERE
        ps.player_id < player_two.id AND (
            SELECT id
            FROM matches
            WHERE
                (
                    ps.player_id = winner AND player_two.id = loser
                ) OR (
                    player_two.id = winner AND ps.player_id = loser
                )
        ) IS NULL -- ensure these two players have not met before in the current tournament
    ORDER BY
        player_one_wins DESC,
        player_one_omw DESC,
        player_two_wins DESC,
        player_one_id,
        player_two_id; -- provide the unmatched_pairs results to swiss_pairings() pre-sorted

-- Create Functions
CREATE FUNCTION no_rematches() RETURNS TRIGGER
AS
-- no_rematches() checks to make sure two players aren't facing each other more than once in a tournament
$BODY$
DECLARE
    -- declare variables
    count_rematches int;

BEGIN
    -- set initial values for variables
    count_rematches := 0;

    -- search matches table for any instances of the two players meeting before in this tournament
    SELECT COUNT(*) INTO count_rematches FROM matches WHERE tournament_id = NEW.tournament_id AND (winner = NEW.winner AND loser = NEW.loser) OR (winner = NEW.loser AND loser = NEW.winner);

    IF count_rematches != 0 THEN
        -- raise exception if this is a rematch
        RAISE EXCEPTION 'These two players have faced each other in this tournament before.';
        RETURN NULL;
    ELSE
        -- otherwise let the INSERT continue
        RETURN NEW;
    END IF;
END
$BODY$
LANGUAGE plpgsql;

CREATE FUNCTION winner_equals_loser() RETURNS TRIGGER
AS
-- winner_equals_loser() checks to make sure that a user has not (presumably inadvertently) entered the same player_id for both winner and loser
$BODY$

BEGIN
    IF NEW.winner = NEW.loser THEN
        -- if the player_id is the same for both winner and loser, raise an exception
        RAISE EXCEPTION 'Winner and loser cannot be the same player.';
        RETURN NULL;
    ELSE
        -- otherwise let the INSERT continue
        RETURN NEW;
    END IF;
END
$BODY$
LANGUAGE plpgsql;

CREATE FUNCTION swiss_pairings(tournament int) RETURNS TABLE (player_one_id int, player_one_name text, player_two_id int, player_two_name text)
AS
-- swiss_pairings() generates the set of matched pairs based on:
--     o which players have already faced each other
--     o how many players are in a tournament
--     o whether or not a bye needs to be assigned
--     o player standings as of the time the function is called
$BODY$
DECLARE
    -- declare variables
    i                           int;
    j                        RECORD;
    pairs                       int;
    starting_players        numeric;
    temp_1                      int;
    temp_2                      int;
    is_bye                     bool;
    temp_remaining_rows         int;
    matched_pairs               int;

BEGIN
    -- set initial values for variables
    SELECT COUNT(*) INTO starting_players FROM players WHERE tournament_id = $1;
    pairs := ceil(starting_players / 2);

    is_bye := FALSE;
    IF starting_players % 2 != 0 THEN
        -- This tournament has an odd number of players; we'll need to assign a bye after pairings have been made
        is_bye := TRUE;
    END IF;

    -- establish temp results table; this will ultimately be returned at the end of the function
    CREATE TEMPORARY TABLE temp_results (
        player_one_id    int,
        player_one_name text,
        player_two_id    int,
        player_two_name text
    ) ON COMMIT DROP;

    -- setup complete
    -- generate a list of pairs of players that have not been matched together previously in this tournament
    CREATE TEMPORARY TABLE unmatched_pairs_temp AS SELECT * FROM unmatched_pairs WHERE tournament_id = $1;

    -- if there are an odd # of players, add rows to unmatched_pairs_temp for each player who has not yet had a bye
    IF is_bye THEN
        FOR j IN SELECT * FROM player_standings ps WHERE ps.tournament_id = $1 AND NOT ps.player_id IN (SELECT m.winner FROM matches m WHERE m.loser IS NULL AND m.is_bye = TRUE) LOOP
            INSERT INTO unmatched_pairs_temp (tournament_id, player_one_id, player_one_name, player_two_id, player_two_name, player_one_wins, player_one_omw, player_two_wins) VALUES ($1, j.player_id, j.player_name, NULL, NULL, j.count_wins, j.omw, NULL);
        END LOOP;
    END IF;

    matched_pairs := 0;

    -- outer loop iterates through the number of pairs in this tournament
    -- this function must generate a complete set of pairs (e.g.: a match with 6 players should have 3 pairs)
    FOR i IN 1..pairs LOOP
        -- inner loop iterates through the remaining rows of unmatched pairs
        FOR j IN SELECT * FROM unmatched_pairs_temp LOOP
            temp_1 := j.player_one_id;
            temp_2 := j.player_two_id;

            -- Pick test
            -- make sure that by pairing two players we aren't leaving other players stranded; i.e.: that all remaining unpaired players will have a partner
            SELECT COUNT(*) INTO temp_remaining_rows FROM unmatched_pairs_temp upt WHERE upt.player_one_id != temp_1 AND upt.player_two_id != temp_1 AND upt.player_one_id != temp_2 AND upt.player_two_id != temp_2 OR ((upt.player_one_id != temp_1 AND upt.player_two_id IS NULL) AND (upt.player_one_id != temp_2 AND upt.player_two_id IS NULL));

            IF temp_remaining_rows > 0 OR matched_pairs = pairs - 1 THEN
                -- take the players out of the temp table
                DELETE FROM unmatched_pairs_temp upt WHERE upt.player_one_id = temp_1 OR upt.player_one_id = temp_2 OR upt.player_two_id = temp_1 OR upt.player_two_id = temp_2;

                -- add the pair to the round
                INSERT INTO temp_results (player_one_id, player_one_name, player_two_id, player_two_name) VALUES (temp_1, j.player_one_name, temp_2, j.player_two_name);

                matched_pairs = matched_pairs + 1;

                -- move to next iteration of the outer loop (i)
                EXIT;
            END IF;
        END LOOP;
    END LOOP;

    RETURN QUERY SELECT * FROM temp_results;

    DROP TABLE unmatched_pairs_temp;
END
$BODY$
LANGUAGE plpgsql;

-- Create Triggers
CREATE TRIGGER check_for_rematches
    BEFORE INSERT OR UPDATE
    ON matches
    FOR EACH ROW
    EXECUTE PROCEDURE no_rematches();

CREATE TRIGGER check_for_winner_equals_loser
    BEFORE INSERT OR UPDATE
    ON matches
    FOR EACH ROW
    EXECUTE PROCEDURE winner_equals_loser();
