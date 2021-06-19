from hive.hex import Piece, Color, Location, Direction
from hive.hive import Hive

hive = Hive()

white_queen = hive.create_hex(Piece.QUEEN, Color.WHITE, Location(0, 0, 0))
black_queen = hive.create_hex(Piece.QUEEN, Color.BLACK, Location(1, -1, 0))
white_ant = hive.create_hex(Piece.ANT, Color.WHITE, Location(2, -2, 0))
white_grasshopper = hive.create_hex(Piece.GRASSHOPPER, Color.WHITE, Location(3, -3, 0))
white_spider = hive.create_hex(Piece.SPIDER, Color.WHITE, Location(4, -4, 0))
black_beetle = hive.create_hex(Piece.BEETLE, Color.BLACK, Location(5, -5, 0))
