# Training

These agents need to train. In order to do this, we need to generate large training sets. Each will demonstrate valid moves.

```json
{
    "input": "prompt",
    "output": "response"
}
```

## Cases that we need to cover

A script will generate samples of these scenarios below. Provide the agent the full prompt each time. Do not save the training set in git but instead save the script which generates and make sure that a seed allows for deterministic train set generates.

- Playing cards
  - Wild cards -> change color (make sure you have that color in your hand)
  - Wild cards -> same color (make sure you have that color in your hand)
  - Regular cards -> same symbol
  - Regular cards -> same color
- Drawing cards
  - When you need to (make sure to message agent)
  - When you do not need to
- Yell UNO
  - When you have one card in hand
  - When someone else has one card in hand

## Questions

- Should we balance the set by actions that probability that the action would be taken in a regular game?
