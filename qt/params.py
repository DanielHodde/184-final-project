PARAMS = [
    dict(
        name="noise",
        type="list",
        limits=["perlin", "fractal-perlin"],
        default="perlin",
        children=[
            dict(name="height scale", type="float", default=10, min=0, max=200),
        ],
    ),
    dict(
        name="style-transfer",
        type="bool",
        default=False,
    ),
    dict(name="trees", type="bool", default=False),
]
