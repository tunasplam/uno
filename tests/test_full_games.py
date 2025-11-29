from uno import UnoServer

def test_one_game():
    # TODO this may require trained agents first.
    server = UnoServer(players=4, player_starting_hand=7)
    server.play_game()
    # only one agent should have won.
    assert sum(p.result for p in server.players) == 1

def test_one_hundred_games():
    return
