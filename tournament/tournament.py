#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#

from contextlib import contextmanager
import psycopg2


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


@contextmanager
def get_cursor():
    """
    Helper function to cut down on unnecessary code when creating and closing
    cusrors and database connections. Thanks to the Udacity project review
    team for the suggestion!
    """
    conn = connect()
    cur = conn.cursor()
    try:
        # the yield function here will provide the cursor if there are no
        # errors, so that it can be "return"ed to the calling function
        yield cur
        conn.commit()  # commit any database changes, such as an INSERT
        return
    except:
        raise  # pass any error back to the calling function as is
    finally:
        cur.close()
        conn.close()


def deleteMatches(tournament=0):
    """Remove all the match records from the database.

    Args:
      tournament: the ID of the tournament for which to delete matches; if 0,
                    delete all matches in all tournaments
    """
    sql = 'DELETE FROM matches'
    data = ('',)

    if (type(tournament) is int and tournament != 0):
        # if function is called with a tournament specified, only delete the
        # matches in that tournament
        sql += ' WHERE tournament_id = %s'
        data = (tournament,)  # prevents SQL injection

    with get_cursor() as cursor:
        cursor.execute(sql, data)


def deletePlayers():
    """Remove all the player records from the database.

    This will also delete the player-to-tournament associations for the
    deleted players.
    """
    sql = 'DELETE FROM registrants'
    with get_cursor() as cursor:
        cursor.execute(sql)


def createTournament(t_name):
    """Adds a tournament to the database.

    The database assigns a unique serial id number for the tournament.

    Args:
      name: the name of the tournament (need not be unique).
    """
    # use "RETURNING id" to make sure to return the tournament ID so
    # we can pass it back to the calling function (i.e.: in case we
    # want to assign a player to that tournament)
    sql = 'INSERT INTO tournaments (name) VALUES (%s) RETURNING id'
    data = (t_name,)  # prevents SQL injection

    with get_cursor() as cursor:
        cursor.execute(sql, data)
        tournament_id = cursor.fetchone()[0]

    return tournament_id


def deleteTournament(tournament=0):
    """Remove one or all tournaments from the database. This will remove all
        matches associated with the deleted tournament(s) as well.

    Args:
      tournament: the ID of the tournament to be deleted; if 0, delete all
    """
    sql = 'DELETE FROM tournaments'
    data = ('',)

    if (type(tournament) is int and tournament != 0):
        # if function is called with a tournament specified, only delete
        # that tournament; otherwise, delete all tournaments
        sql += ' WHERE id = %s'
        data = (tournament,)  # prevents SQL injection

    with get_cursor() as cursor:
        cursor.execute(sql, data)


def countPlayers(tournament=None):
    """Returns the number of players currently registered.

    If the ID of a tournament is passed to the function, the result will
    be a count of players just in that tournament.

    Args:
      tournament: ID of the tournament for which to count players (optional)
    """
    data = ('',)

    if (tournament is not None):
        # if function is called with a tournament specified, only count the
        # players in that tournament
        sql = 'SELECT COUNT(*) FROM players WHERE tournament_id = %s'
        data = (tournament,)  # prevents SQL injection
    else:
        # otherwise, return a count of all players in all tournaments
        sql = 'SELECT COUNT(*) FROM players'

    with get_cursor() as cursor:
        cursor.execute(sql, data)
        player_count = cursor.fetchone()[0]

    return player_count


def registerPlayer(p_name, tournament=None):
    """Adds a player to the tournament database.

    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)

    This function may be used to add a player to a tournament simultaneously
    by passing the ID of the tournament to the function.

    Args:
      name: the player's full name (need not be unique).
      tournament: the ID of the tournament to register the player in (optional)
    """
    # use "RETURNING" to make sure to return the registrant ID so
    # we can pass it back to the calling function (i.e.: in case we
    # want to assign that registrant to a tournament)
    sql = 'INSERT INTO registrants (name) VALUES (%s) RETURNING *'
    data = (p_name,)  # prevents SQL injection

    with get_cursor() as cursor:
        cursor.execute(sql, data)
        # put the new registrant data into new_player
        new_player = cursor.fetchone()[0]

    if (tournament and type(tournament) is int):
        # if tournament is specified, user wants this registrant to be added
        # as a player to a tournament; so, do that
        sql = 'INSERT INTO players (tournament_id, registrant_id) VALUES '
        sql += '(%s, %s)'
        data = (tournament, new_player,)  # prevents SQL injection
        with get_cursor() as cursor:
            cursor.execute(sql, data)


def assignPlayer(registrant, tournament):
    """Assigns a registrant to a tournament

    Only used if the player was not associated with a tournament when s/he
    was registered; also only used for existing players.

    Args:
      registrant: ID of the player in the players table
      tournament: ID of the tournament
    """
    # check function inputs to make sure they're of the right data type
    if (type(registrant) is not int or type(tournament) is not int):
        return '''
        Either the registrant or the tournament you entered is invalid.
        '''

    sql = 'INSERT INTO players (tournament_id, registrant_id) VALUES (%s, %s)'
    data = (tournament, registrant,)  # prevents SQL injection
    with get_cursor() as cursor:
        cursor.execute(sql, data)


def unAssignPlayer(registrant, tournament):
    """Removes a registrant from a tournament

    Args:
      registrant: ID of the player in the players table
      tournament: ID of the tournament
    """
    # check function inputs to make sure they're of the right data type
    if (type(registrant) is not int or type(tournament) is not int):
        return 'Either the registrant or tournament you entered is invalid.'

    # note that registrant is not deleted, so can be assigned to other
    # tournaments
    sql = 'DELETE FROM players WHERE tournament_id = %s AND player_id = %s'
    data = (tournament, registrant,)  # prevents SQL injection

    with get_cursor() as cursor:
        cursor.execute(sql, data)


def playerStandings(tournament):
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place,
    or a player tied for first place if there is currently a tie.

    Args:
      tournament: the ID of the tournament for which to display standings

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches, omw):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
        omw: the number of wins of all the player's previous opponents
    """
    # check function input to make sure it's of the right data type
    if (type(tournament) is not int):
        return 'Tournament is invalid (must be a number).'

    # execute the view player_standings to generate the standings list
    sql = 'SELECT player_id, player_name, count_wins, count_matches, omw FROM '
    sql += 'player_standings WHERE tournament_id = %s'
    data = (tournament,)  # prevents SQL injection

    with get_cursor() as cursor:
        cursor.execute(sql, data)
        players = cursor.fetchall()

    player_list = []

    # build the list of tuples to pass back to the calling function
    for player in players:
        player_list.append(player)

    return player_list


def reportMatch(winner, loser, tournament, is_tie=False):
    """Records the outcome of a single match between two players.

    In the case of a tie, "is_tie" will be True and neither of the
    two players will record a win for the match.

    If loser is 0, this is a bye. Byes occur when there is an odd number
    of players, meaning that one player in each round will not have a
    partner. A bye counts as a win, and for that reason no player should
    receive a bye more than once in a tournament. The system prevents that
    from happening.

    Args:
      winner: the id number of the tournament_player who won
      loser: the id number of the tournament_player who lost
      tournament: the ID of the tournament this match was played in
      is_tie: if the match results in a tie, this value is True
    """
    # check function inputs to make sure they're of the right data type
    if (type(winner) is not int):
        return 'Winner is invalid (must be a number).'
    elif (type(loser) is not int):
        return 'Loser is invalid (must be a number).'
    elif (type(tournament) is not int):
        return 'Tournament is invalid (must be a number).'
    elif (type(is_tie) is not bool):
        err_msg = 'The entry for whether this match was a tie is invalid '
        err_msg += '(must be "True" or "False" (or blank)).'
        return err_msg

    if (loser != 0):
        # if a loser player ID is passed to the function, this is a normal
        # match; record it in the database
        sql = 'INSERT INTO matches (winner, loser, tournament_id, is_tie) '
        sql += 'VALUES (%s, %s, %s, %s)'
        data = (winner, loser, tournament, is_tie,)  # prevents SQL injection
    else:
        # if 0 is passed to the function as the loser, this is a bye match;
        # record it as such in the database (see docstring for definition
        # of a bye)
        sql = 'INSERT INTO matches (winner, tournament_id, is_bye) VALUES '
        sql += '(%s, %s, True)'
        data = (winner, tournament,)  # prevents SQL injection

    with get_cursor() as cursor:
        cursor.execute(sql, data)


def swissPairings(tournament):
    """Returns a list of pairs of players for the next round of a match.

    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.

    If there are an odd number of players, one player in each round will
    receive a "bye" for that round which counts as a win. No player will
    receive more than one bye in a tournament.

    This function also ensures that two players are never paired together
    more than once in a tournament.

    Args:
      tournament: the ID of the tournament for which to generate pairings

    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first tournament_player's unique id
        name1: the first player's name
        id2: the second tournament_player's unique id
        name2: the second player's name
    """
    # check function input to make sure it's of the right data type
    if (type(tournament) is not int):
        return 'Tournament is invalid (must be a number).'

    # call the function swiss_pairings(), passing in the tournament ID
    # swiss_pairings() checks to see which players have already been matched
    # up and gives us a new round of pairings
    sql = 'SELECT * FROM swiss_pairings(%s)'
    data = (tournament,)  # prevents SQL injection

    with get_cursor() as cursor:
        cursor.execute(sql, data)
        pairs = cursor.fetchall()

    pair_list = []

    # build the list of tuples to return to the calling function
    for pair in pairs:
        pair_list.append(pair)

    return pair_list
