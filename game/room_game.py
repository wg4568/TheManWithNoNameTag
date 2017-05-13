import stellar
import resources
import tools
import math
import itertools
import random
import numpy
import player

class GridTile(stellar.objects.Object):
	def __init__(self, x, y, typ=0, tilesize=32):
		stellar.objects.Object.__init__(self)

		self.disable()

		self.tilesize = tilesize
		self.type = typ
		self.grid_x = x
		self.grid_y = y

		self.solid = self.type not in resources.NON_SOLID_SPRITES

		sprite = resources.TILE_REFERENCE[self.type]

		self.add_sprite("default", sprite)
		self.add_sprite("blank", resources.TILE_REFERENCE[0, 0])
		self.set_sprite("default")

	def draw(self):
		self.get_current_sprite().draw(self.room, self.get_position(), self.scale)

	def _draw(self):
		pass

class GameObject(stellar.objects.Object):
	def __init__(self):
		stellar.objects.Object.__init__(self)

		self.game_x = 0
		self.game_y = 0

	def move_to(self, x, y):
		self.game_x = x
		self.game_y = y

	def move_by(self, dx, dy):
		self.game_x += dx
		self.game_y += dy

	def draw(self):
		self.get_current_sprite().draw(self.room, self.get_position(), self.scale)

	def _draw(self):
		pass

class Zombie(GameObject):
	def __init__(self):
		GameObject.__init__(self)
		self.move_speed = 20

		walk_left = stellar.sprites.Animation(*resources.ZOMBIE_LEFT)
		walk_right = stellar.sprites.Animation(*resources.ZOMBIE_RIGHT)

		walk_left.set_rate(5)
		walk_right.set_rate(5)

		walk_left.add_event([3, 5, 7], self.step_left)
		walk_right.add_event([3, 5, 7], self.step_right)

		self.add_sprite("walk_left", walk_left)
		self.add_sprite("walk_right", walk_right)
		self.set_sprite("walk_right")

	def step_left(self):
		# self.move_by(-self.move_speed, 0)
		pass

	def step_right(self):
		# self.move_by(self.move_speed, 0)
		pass

	def logic(self):
		self.move_by(1, 0)

class Room(stellar.rooms.Room):
	def __init__(self):
		stellar.rooms.Room.__init__(self)
		self.game_objects = []
		self.zombies = []

		self.grid = {}

		self.tilesize = float(resources.TILESIZE)


		self.cam_x = 0
		self.cam_y = 0

		self.max_speed = 9
		self.slowed_speed = 7

		self.move_speed = self.max_speed

		for x, y in resources.LEVEL_TEST:
			nt = GridTile(x, y, typ=resources.LEVEL_TEST[x, y], tilesize=self.tilesize)
			self.add_object(nt)
			self.grid[x, y] = nt


		self.playerarm = player.PlayerArm()
		self.player = player.Player(self.playerarm)
		self.playerhb = player.PlayerMovementHitbox(self.player)
		self.add_object(self.player)
		self.add_object(self.playerarm)
		self.add_object(self.playerhb)

		self.add_zombie(300, 300)

	def add_zombie(self, *posn):
		nz = Zombie()
		nz.move_to(*posn)
		self.zombies.append(nz)
		self.add_gameobject(nz)

	def line_pos(self, x):
		b = self.size[1]
		return (-self.slope * x) + b

	def line_neg(self, x):
		return self.slope * x

	def add_gameobject(self, obj):
		self.add_object(obj)
		self.game_objects.append(obj)

	def on_load(self):
		cntr = self.center()
		self.player.move_to(*cntr)
		self.playerhb.move_to(cntr[0]-(self.playerhb.width/2.0), cntr[1])
		self.slope = self.size[1]/float(self.size[0])

	# Manual draw function
	def _draw(self):
		self.game.screen.fill(self.background)

		drawbuffer = 1
		x_wid = int(math.ceil(self.size[0] / self.tilesize))
		y_wid = int(math.ceil(self.size[1] / self.tilesize))
		cam_gx = int(math.floor(self.cam_x / self.tilesize))
		cam_gy = int(math.floor(self.cam_y / self.tilesize))
		x_range = xrange(cam_gx-drawbuffer, cam_gx+x_wid+drawbuffer)
		y_range = xrange(cam_gy-drawbuffer, cam_gy+y_wid+drawbuffer)

		for x, y in itertools.product(x_range, y_range):
			try:
				obj = self.grid[x, y]
				obj.x = (x * self.tilesize) - self.cam_x
				obj.y = (y * self.tilesize) - self.cam_y
				obj.draw()
			except KeyError:
				pass

		for obj in self.game_objects:
			obj.x = obj.game_x - self.cam_x
			obj.y = obj.game_y - self.cam_y
			obj.draw()

		for fixture, posn in self.fixtures:
			fixture.draw(self, posn)

		for obj in self.objects:
			obj._draw()

		self.draw()

	def control(self, buttons, mousepos):
		mouseX, mouseY = mousepos
		deltaX = 0
		deltaY = 0


		if buttons[stellar.keys.S_HELD][resources.CONTROL_UP]:
			deltaY -= self.move_speed
		if buttons[stellar.keys.S_HELD][resources.CONTROL_DOWN]:
			deltaY += self.move_speed
		if buttons[stellar.keys.S_HELD][resources.CONTROL_LEFT]:
			deltaX -= self.move_speed
		if buttons[stellar.keys.S_HELD][resources.CONTROL_RIGHT]:
			deltaX += self.move_speed

		if deltaY < 0:
			if deltaX < 0:
				self.player.direction = 1
			elif deltaX > 0:
				self.player.direction = 3
			else:
				self.player.direction = 2
		elif deltaY > 0:
			if deltaX < 0:
				self.player.direction = 7
			elif deltaX > 0:
				self.player.direction = 5
			else:
				self.player.direction = 6
		else:
			if deltaX < 0:
				self.player.direction = 8
			elif deltaX > 0:
				self.player.direction = 4
			else:
				self.player.direction = 0

		midX, midY = self.center()
		if mouseY < midY:
			if mouseX < midX:
				self.player.face_direction = 0
			else:
				self.player.face_direction = 1
		else:
			if mouseX < midX:
				self.player.face_direction = 3
			else:
				self.player.face_direction = 2

		self.player.moving = bool(self.player.direction)

		deltaX, deltaY = self.playerhb.check_valid(deltaX, deltaY)

		pos = self.line_pos(mouseX) > mouseY
		neg = self.line_neg(mouseX) > mouseY

		if self.player.backwards:
			self.move_speed = self.slowed_speed
		else:
			self.move_speed = self.max_speed

		if (pos) and (not neg):
			self.player.m_direction = 0
		if (pos) and (neg):
			self.player.m_direction = 1
		if (not pos) and (neg):
			self.player.m_direction = 2
		if (not pos) and (not neg):
			self.player.m_direction = 3

		self.cam_x += deltaX
		self.cam_y += deltaY

	def draw(self):
		self.draw_text("%s, %s" % self.game.mousepos, (10, 10), resources.FONT_ARIAL_WHITE_12)
		# Debug 'crosshair'
		# self.draw_rect((255, 255, 255), list(self.center()) + [3, 3])
