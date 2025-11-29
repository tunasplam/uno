from uno import UnoServer

def test_draw():
    server = UnoServer(players=2, player_starting_hand=7, forced_top_card="R0")
    for p in server.players:
        assert len(p.hand) == 7

    server.process_request({
        "playerID": 1,
        "action": "Draw card",
    })

    assert len(server.get_player(1).hand) == 8
    assert len(server.get_player(2).hand) == 7

def test_play_card_same_color():
    server = UnoServer(players=2, player_starting_hand=7, forced_top_card="Y5")
    # force a card in the player's hand to be Y7
    server.players[0].hand[0] = "Y7"
    server.players[0].take_action({"action": "Play card", "card": "Y7"})
    server.process_request(server.request_queue[0])
    assert len(server.deck.discard_pile) == 2
    assert server.deck.top_card_on_discard_pile() == "Y7"
    assert len(server.get_player(1).hand) == 6
    assert len(server.get_player(2).hand) == 7

def test_play_card_same_value():
    server = UnoServer(players=2, player_starting_hand=7, forced_top_card="Y5")
    server.players[0].hand[0] = "B5"
    server.players[0].take_action({"action": "Play card", "card": "B5"})
    server.process_request(server.request_queue[0])
    assert len(server.deck.discard_pile) == 2
    assert server.deck.top_card_on_discard_pile() == "B5"
    assert len(server.get_player(1).hand) == 6
    assert len(server.get_player(2).hand) == 7

def test_play_reverse():
    server = UnoServer(players=3, player_starting_hand=7, forced_top_card="Y5")
    server.players[0].hand[0] = "YR"
    server.players[0].take_action({"action": "Play card", "card": "YR"})
    server.process_request(server.request_queue[0])
    assert server.next_player.id == 3

def test_play_wild():
    server = UnoServer(players=2, player_starting_hand=7, forced_top_card="B5")
    server.get_player(1).hand[0] = "WW"
    server.get_player(2).hand[0] = "R7"
    server.get_player(1).take_action({"action": "Play card", "card": "WW", "nextColor": "R"})
    server.process_request(server.request_queue.popleft())
    server.get_player(2).take_action({"action": "Play card", "card": "R7"})
    server.process_request(server.request_queue.popleft())
    assert len(server.get_player(1).hand) == 6
    assert len(server.get_player(2).hand) == 6

def test_play_draw_two():
    server = UnoServer(players=2, player_starting_hand=7, forced_top_card="B5")
    server.get_player(1).hand[0] = "BD"
    server.get_player(1).take_action({"action": "Play card", "card": "BD"})
    server.process_request(server.request_queue.popleft())
    assert server.must_draw_count == 2
    assert len(server.get_player(1).hand) == 6

def test_play_draw_four():
    server = UnoServer(players=2, player_starting_hand=7, forced_top_card="B5")
    server.get_player(1).hand[0] = "WF"
    server.get_player(1).take_action({"action": "Play card", "card": "WF", "nextColor": "R"})
    server.process_request(server.request_queue.popleft())
    assert server.must_draw_count == 4
    assert len(server.get_player(1).hand) == 6

def test_play_card_when_should_draw():
    server = UnoServer(players=2, player_starting_hand=7, forced_top_card="B5")
    server.get_player(1).hand[0] = "BD"
    server.get_player(2).hand[0] = "B8"
    server.get_player(1).take_action({"action": "Play card", "card": "BD"})
    server.process_request(server.request_queue.popleft())
    server.get_player(2).take_action({"action": "Play card", "card": "B8"})
    server.process_request(server.request_queue.popleft())
    assert server.get_player(2).message_queue == ["You must draw a card."]
    assert len(server.get_player(1).hand) == 6
    assert len(server.get_player(2).hand) == 7

def test_play_skip():
    server = UnoServer(players=3, player_starting_hand=7, forced_top_card="B5")
    server.get_player(1).hand[0] = "BS"
    server.get_player(1).take_action({"action": "Play card", "card": "BS"})
    server.process_request(server.request_queue.popleft())
    assert server.next_player == server.get_player(3)

def test_uno_shield():
    server = UnoServer(players=3, player_starting_hand=7, forced_top_card="B5")
    server.get_player(1).hand = ["B5"]
    server.get_player(1).take_action({"action": "Yell UNO"})
    server.process_request(server.request_queue.popleft())
    assert server.get_player(1).is_shielded

def test_uno_catch():
    server = UnoServer(players=3, player_starting_hand=7, uno_penalty=7, forced_top_card="B5")
    server.get_player(1).hand = ["B5"]
    server.get_player(2).take_action({"action": "Yell UNO"})
    server.process_request(server.request_queue.popleft())
    assert len(server.get_player(1).hand) == 8
    assert server.next_player == server.get_player(1)
