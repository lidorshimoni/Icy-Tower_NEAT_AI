import pygame


from IceSprite import IceSprite
from Utils import message_display

pygame.init()

from copy import deepcopy

class Platform:
	color = (255, 100, 100)
	def __init__(self, x, y, width, height, index):
		self.x = x
		self.index = index
		self.y = y
		self.height = height
		self.width = width
		self.rect = pygame.Rect(x, y, width, height)
		# self.collected_score = False
		self.collected_score = {}

	def draw(self, game_display, camera):
		rect = deepcopy(self.rect)
		rect.top -= camera.y
		pygame.draw.rect(game_display, self.color, rect)
		for i in range(self.x, self.x+self.width, 10):
			sprite = IceSprite([i, self.y - camera.y])
			game_display.blit(sprite.image, sprite.rect)

		color = (200, 200, 200)
		# if self.collected_score:
		# 	color = (200,0,0)
		message_display(game_display, str(self.index), self.x+self.width/2, self.y - camera.y-5, 30, color)

	def collect_score(self, player):
		if player in self.collected_score.keys():
			return True

		self.collected_score[player] = True
		return False

