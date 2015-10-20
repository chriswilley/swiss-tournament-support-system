#!/usr/bin/env python
#
# Test cases for tournament.py

from tournament import *


def testDeleteMatches():
    deleteMatches()
    print "1. Old matches can be deleted."


def testDelete():
    deleteMatches()
    deletePlayers()
    deleteTournament()
    print "2. Player records can be deleted."


def testCount():
    deleteMatches()
    deletePlayers()
    deleteTournament()
    c = countPlayers()
    if c == '0':
        raise TypeError(
            "countPlayers() should return numeric zero, not string '0'.")
    if c != 0:
        raise ValueError("After deleting, countPlayers should return zero.")
    print "3. After deleting, countPlayers() returns zero."


def testRegister():
    deleteMatches()
    deletePlayers()
    deleteTournament()
    tournament_id = createTournament("Breakfast of Champions")
    registerPlayer("Chandra Nalaar", tournament_id)
    c = countPlayers()
    if c != 1:
        raise ValueError(
            "After one player registers, countPlayers() should be 1.")
    print "4. After registering a player, countPlayers() returns 1."


def testRegisterCountDelete():
    deleteMatches()
    deletePlayers()
    deleteTournament()
    tournament_id = createTournament('Ship of Fools')
    registerPlayer("Markov Chaney", tournament_id)
    registerPlayer("Joe Malik", tournament_id)
    registerPlayer("Mao Tsu-hsi", tournament_id)
    registerPlayer("Atlanta Hope", tournament_id)
    c = countPlayers()
    if c != 4:
        raise ValueError(
            "After registering four players, countPlayers should be 4.")
    deletePlayers()
    c = countPlayers()
    if c != 0:
        raise ValueError("After deleting, countPlayers should return zero.")
    print "5. Players can be registered and deleted."


def testStandingsBeforeMatches():
    """
    Test modified to include Opponent Match Wins in standings list
    """
    deleteMatches()
    deletePlayers()
    deleteTournament()
    tournament_id = createTournament('Bonus Round')
    registerPlayer("Melpomene Murray", tournament_id)
    registerPlayer("Randy Schwartz", tournament_id)
    standings = playerStandings(tournament_id)
    if len(standings) < 2:
        raise ValueError(
            "Players should appear in playerStandings even before "
            "they have played any matches.")
    elif len(standings) > 2:
        raise ValueError("Only registered players should appear in standings.")
    if len(standings[0]) != 5:
        raise ValueError("Each playerStandings row should have five columns.")
    [(id1, name1, wins1, matches1, omw1),
        (id2, name2, wins2, matches2, omw2)] = standings
    if matches1 != 0 or matches2 != 0 or wins1 != 0 or wins2 != 0:
        raise ValueError(
            "Newly registered players should have no matches or wins.")
    if set([name1, name2]) != set(["Melpomene Murray", "Randy Schwartz"]):
        raise ValueError(
            "Registered players' names should appear in standings, "
            "even if they have no matches played.")
    print (
        "6. Newly registered players appear in the standings with no matches.")


def testReportMatches():
    """
    Test modified to include Opponent Match Wins in standings list
    """
    deleteMatches()
    deletePlayers()
    deleteTournament()
    tournament_id = createTournament('High Noon')
    registerPlayer("Bruno Walton", tournament_id)
    registerPlayer("Boots O'Neal", tournament_id)
    registerPlayer("Cathy Burton", tournament_id)
    registerPlayer("Diane Grant", tournament_id)
    standings = playerStandings(tournament_id)
    [id1, id2, id3, id4] = [row[0] for row in standings]
    reportMatch(id1, id2, tournament_id)
    reportMatch(id3, id4, tournament_id)
    standings = playerStandings(tournament_id)
    for (i, n, w, m, o) in standings:
        if m != 1:
            raise ValueError("Each player should have one match recorded.")
        if i in (id1, id3) and w != 1:
            raise ValueError("Each match winner should have one win recorded.")
        elif i in (id2, id4) and w != 0:
            raise ValueError(
                "Each match loser should have zero wins recorded.")
        elif i in (id2, id4) and o != 1:
            raise ValueError(
                "Each match loser after the first round "
                "should have one OMW recorded.")
    print "7. After a match, players have updated standings."


def testReportMatchesWithTies():
    """
    If a match results in a tie, do not record a win for either of
    those two players but do record the match.
    """
    deleteMatches()
    deletePlayers()
    deleteTournament()
    tournament_id = createTournament('High Noon Redux')
    registerPlayer("Bruno Walton", tournament_id)
    registerPlayer("Boots O'Neal", tournament_id)
    registerPlayer("Cathy Burton", tournament_id)
    registerPlayer("Diane Grant", tournament_id)
    standings = playerStandings(tournament_id)
    [id1, id2, id3, id4] = [row[0] for row in standings]
    reportMatch(id1, id2, tournament_id)
    reportMatch(id3, id4, tournament_id, True)
    standings = playerStandings(tournament_id)
    for (i, n, w, m, o) in standings:
        if m != 1:
            raise ValueError("Each player should have one match recorded.")
        if i in (id1,) and w != 1:
            raise ValueError("Each match winner should have one win recorded.")
        elif i in (id2, id3, id4) and w != 0:
            raise ValueError(
                "Each match loser should have zero wins recorded.")
        elif i in (id2,) and o != 1:
            raise ValueError(
                "Each match loser after the first round "
                "should have one OMW recorded, except for ties.")
    print "    7a. Player standings correctly account for ties."


def testReportMatchesNoRematch():
    """
    System should throw an error if user attempts to record a rematch.
    """
    deleteMatches()
    deletePlayers()
    deleteTournament()
    tournament_id = createTournament('High Noon Redux.1')
    registerPlayer("Bruno Walton", tournament_id)
    registerPlayer("Boots O'Neal", tournament_id)
    registerPlayer("Cathy Burton", tournament_id)
    registerPlayer("Diane Grant", tournament_id)
    standings = playerStandings(tournament_id)
    [id1, id2, id3, id4] = [row[0] for row in standings]
    reportMatch(id1, id2, tournament_id)
    err = ''
    try:
        reportMatch(id1, id2, tournament_id)
    except psycopg2.InternalError as e:
        err = e
        pass
    expected_err = 'These two players have faced each other in '
    expected_err += 'this tournament before.\n'
    if str(err) != expected_err:
        raise ValueError("System did not prevent a rematch.")
    print "    7b. System prevents rematches."


def testPairings():
    deleteMatches()
    deletePlayers()
    deleteTournament()
    tournament_id = createTournament('Race of the Century')
    registerPlayer("Twilight Sparkle", tournament_id)
    registerPlayer("Fluttershy", tournament_id)
    registerPlayer("Applejack", tournament_id)
    registerPlayer("Pinkie Pie", tournament_id)
    standings = playerStandings(tournament_id)
    [id1, id2, id3, id4] = [row[0] for row in standings]
    reportMatch(id1, id2, tournament_id)
    reportMatch(id3, id4, tournament_id)
    pairings = swissPairings(tournament_id)
    if len(pairings) != 2:
        raise ValueError(
            "For four players, swissPairings should return two pairs.")
    [(pid1, pname1, pid2, pname2), (pid3, pname3, pid4, pname4)] = pairings
    correct_pairs = set([frozenset([id1, id3]), frozenset([id2, id4])])
    actual_pairs = set([frozenset([pid1, pid2]), frozenset([pid3, pid4])])
    if correct_pairs != actual_pairs:
        raise ValueError(
            "After one match, players with one win should be paired.")
    print "8. After one match, players with one win are paired."


def testOddPairings():
    """
    With an odd number of players, system should correctly assign byes.
    """
    deleteMatches()
    deletePlayers()
    deleteTournament()
    tournament_id = createTournament('Race of the Century Part Deux')
    registerPlayer("Twilight Sparkle", tournament_id)
    registerPlayer("Fluttershy", tournament_id)
    registerPlayer("Applejack", tournament_id)
    registerPlayer("Pinkie Pie", tournament_id)
    registerPlayer("Purple Dinosaur", tournament_id)
    standings = playerStandings(tournament_id)
    [id1, id2, id3, id4, id5] = [row[0] for row in standings]
    reportMatch(id1, id2, tournament_id)
    reportMatch(id3, id4, tournament_id)
    reportMatch(id5, 0, tournament_id)
    pairings = swissPairings(tournament_id)
    if len(pairings) != 3:
        raise ValueError(
            "For five players, swissPairings should return three pairs.")
    [
        (pid1, pname1, pid2, pname2),
        (pid3, pname3, pid4, pname4),
        (pid5, pname5, pid6, pname6)
    ] = pairings
    correct_pairs = set([
        frozenset([id1, id3]),
        frozenset([id2, id5]),
        frozenset([id4, None])
    ])
    actual_pairs = set([
        frozenset([pid1, pid2]),
        frozenset([pid3, pid4]),
        frozenset([pid5, None])
    ])
    if correct_pairs != actual_pairs:
        raise ValueError(
            "After one match, players with one win should be paired.")
    print ("    8a. After one match, players with one win are paired "
           "and bye is assigned.")


if __name__ == '__main__':
    testDeleteMatches()
    testDelete()
    testCount()
    testRegister()
    testRegisterCountDelete()
    testStandingsBeforeMatches()
    testReportMatches()
    testReportMatchesWithTies()
    testReportMatchesNoRematch()
    testPairings()
    testOddPairings()
    print "Success!  All tests pass!"
