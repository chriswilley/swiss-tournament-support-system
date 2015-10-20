#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#

import bleach
import psycopg2


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def deleteMatches(tournament=0):
    """Remove all the match records from the database.

    Args:
      tournament: the ID of the tournament for which to delete matches; if 0,
                    delete all matches in all tournaments
    """
    conn = connect()
    cur = conn.cursor()
    sql = 'DELETE FROM matches'
    if (type(tournament) is int and tournament != 0):
        sql += ' WHERE tournament_id = ' + tournament
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()


def deletePlayers():
    """Remove all the player records from the database.

    This will also delete the player-to-tournament associations for the
    deleted players.
    """
    conn = connect()
    cur = conn.cursor()
    sql = 'DELETE FROM registrants'
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()


def createTournament(t_name):
    """Adds a tournament to the database.

    The database assigns a unique serial id number for the tournament.

    Args:
      name: the name of the tournament (need not be unique).
    """
    conn = connect()
    cur = conn.cursor()
    sql = 'INSERT INTO tournaments (name) VALUES (%s) RETURNING id'
    data = (bleach.clean(t_name),)
    cur.execute(sql, data)
    tournament_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return tournament_id


def deleteTournament(tournament=0):
    """Remove one or all tournaments from the database. This will remove all
        matches associated with the deleted tournament(s) as well.

    Args:
      tournament: the ID of the tournament to be deleted; if 0, delete all
    """
    conn = connect()
    cur = conn.cursor()
    sql = 'DELETE FROM tournaments'
    if (type(tournament) is int and tournament != 0):
        sql += ' WHERE id = ' + tournament
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()


def countPlayers(tournament=None):
    """Returns the number of players currently registered.

    If the ID of a tournament is passed to the function, the result will
    be a count of players just in that tournament.

    Args:
      tournament: ID of the tournament for which to count players (optional)
    """
    conn = connect()
    cur = conn.cursor()
    if (tournament is not None):
        sql = 'SELECT COUNT(*) FROM players WHERE tournament_id = '
        sql += tournament
    else:
        sql = 'SELECT COUNT(*) FROM players'
    cur.execute(sql)
    player_count = cur.fetchone()[0]
    cur.close()
    conn.close()
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
    conn = connect()
    cur = conn.cursor()
    sql = 'INSERT INTO registrants (name) VALUES (%s) RETURNING *'
    data = (bleach.clean(p_name),)
    cur.execute(sql, data)
    if (tournament and type(tournament) is int):
        new_player = cur.fetchone()[0]
        sql = 'INSERT INTO players (tournament_id, registrant_id) VALUES '
        sql += '(%s, %s)'
        data = (tournament, new_player,)
        cur.execute(sql, data)
    conn.commit()
    cur.close()
    conn.close()


def assignPlayer(player, tournament):
    """Assigns a player to a tournament

    Only used if the player was not associated with a tournament when s/he
    was registered; also only used for existing players.

    Args:
      player: ID of the player in the players table
      tournament: ID of the tournament
    """
    if (type(player) is not int or type(tournament) is not int):
        return 'Either the player or the tournament you entered is invalid.'
    conn = connect()
    cur = conn.cursor()
    sql = 'INSERT INTO tournament_players (tournament_id, player_id) '
    sql += 'VALUES (%s, %s)'
    data = (tournament, player,)
    try:
        cur.execute(sql, data)
        conn.commit()
    except psycopg2.Error as e:
        return e
    cur.close()
    conn.close()


def unAssignPlayer(player, tournament):
    """Removes a player from a tournament

    Args:
      player: ID of the player in the players table
      tournament: ID of the tournament
    """
    if (type(player) is not int or type(tournament) is not int):
        return 'Either the player or the tournament you entered is invalid.'
    conn = connect()
    cur = conn.cursor()
    sql = 'DELETE FROM tournament_players WHERE tournament_id = %s AND '
    sql += 'player_id = %s'
    data = (tournament, player,)
    try:
        cur.execute(sql, data)
        conn.commit()
    except psycopg2.Error as e:
        return e
    cur.close()
    conn.close()


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
    if (type(tournament) is not int):
        return 'Tournament is invalid (must be a number).'

    conn = connect()
    cur = conn.cursor()
    sql = 'SELECT player_id, player_name, count_wins, count_matches, omw FROM '
    sql += 'player_standings WHERE tournament_id = %s'
    data = (tournament,)
    cur.execute(sql, data)
    players = cur.fetchall()
    player_list = []
    for player in players:
        player_list.append(player)
    cur.close()
    conn.close()
    return player_list


def reportMatch(winner, loser, tournament, is_tie=False):
    """Records the outcome of a single match between two players.

    In the case of a tie, "is_tie" will be True and neither of the
    two players will record a win for the match.

    If loser is 0, this is a bye.

    Args:
      winner: the id number of the tournament_player who won
      loser: the id number of the tournament_player who lost
      tournament: the ID of the tournament this match was played in
      is_tie: if the match results in a tie, this value is True
    """
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

    conn = connect()
    cur = conn.cursor()

    if (loser != 0):
        sql = 'INSERT INTO matches (winner, loser, tournament_id, is_tie) '
        sql += 'VALUES (%s, %s, %s, %s)'
        data = (winner, loser, tournament, is_tie,)
    else:
        sql = 'INSERT INTO matches (winner, tournament_id, is_bye) VALUES '
        sql += '(%s, %s, True)'
        data = (winner, tournament,)

    try:
        cur.execute(sql, data)
        conn.commit()
    except psycopg2.Error, e:
        return e.pgerror

    cur.close()
    conn.close()


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
    if (type(tournament) is not int):
        return 'Tournament is invalid (must be a number).'

    conn = connect()
    cur = conn.cursor()
    sql = 'SELECT * FROM swiss_pairings(%s)'
    data = (tournament,)
    cur.execute(sql, data)
    pairs = cur.fetchall()
    pair_list = []
    for pair in pairs:
        pair_list.append(pair)
    cur.close()
    conn.close()
    return pair_list
