from svg import Parser, Rasterizer
import pygame


def load_svg(filename, surface, position, size=None):
    if size is None:
        w = surface.get_width()
        h = surface.get_height()
    else:
        w, h = size
    svg = Parser.parse_file(filename)
    rast = Rasterizer()
    buff = rast.rasterize(svg, w, h)
    image = pygame.image.frombuffer(buff, (w, h), 'ARGB')
    surface.blit(image, position)