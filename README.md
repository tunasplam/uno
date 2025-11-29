# Uno

There are players. Each player has a Hand of Cards. There is a shuffled Deck.

Each card has a Color and a Value. The Value indicates what it is able to do.

## Torch and CUDA

I am using an older NVIDIA graphics card so notice that `pyproject.toml` has been configured to search for a lower
version of CUDA. If you have a newer graphics card then you can get rid of these requirements and use latest torch.
If you have an older version, the terminal warnings upon running will let you know which index url to use for `cu`.
