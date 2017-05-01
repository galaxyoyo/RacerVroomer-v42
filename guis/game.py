#coding : utf-8

import tkinter as tk
from PIL import Image, ImageTk
from guis import GUI, mainMenu

import cars, utils
import messages as msgs
from audio import AudioPlayer
import math
from threading import Thread

class Game(GUI):
	def __init__(self, window, builder):
		GUI.__init__(self)

		self.window = window
		self.raw_car = builder.car
		self.map = builder.map

		self.width, self.height = window.winfo_reqwidth(), window.winfo_reqheight()
		if window.state() == "zoomed":
			self.width, self.height = window.winfo_screenwidth(), window.winfo_screenheight()
		self.canvas = tk.Canvas(window, width = window.winfo_screenwidth(), height = window.winfo_screenheight(), bg = "green")

		img_temp = Image.open("images/maps/" + self.map.img_file)
		img_temp = img_temp.convert("RGBA")
		img_temp = img_temp.resize((self.width, self.height), Image.ANTIALIAS)
		self.background_img = ImageTk.PhotoImage(img_temp)
		self.background = self.canvas.create_image(self.width, self.height, image = self.background_img)
		self.canvas.focus_set()
		self.canvas.pack()
		self.canvas.coords(self.background, self.width / 2, self.height / 2)
		window.bind("<Configure>", lambda event : self.on_resize(event))

		self.time_label = tk.Label(window, text = "00:00:00.000", font = ("Plantagenet Cherokee", 24), fg = "white", bg = "black")
		self.time_label.place(x = 0, y = 0)
		self.appendChild(self.time_label)

		self.lap = 0
		self.lap_label = tk.Label(window, text = msgs.LAP_NUMBER.get().format(self.lap, self.map.max_laps), font = ("Plantagenet Cherokee", 24), fg ="white", bg ="black")
		self.lap_label.place(x = 0, y = self.time_label.winfo_reqheight(), width = self.time_label.winfo_reqwidth())
		self.appendChild(self.lap_label)

		self.car = Car(window, self)
		self.time = -1

		self.appendChild(self.canvas)

	def on_resize(self, event):
		if self.car.paused or self.car.thread.stopped:
			return

		self.width, self.height = event.width, event.height
		self.canvas.delete(self.background)
		img_temp = Image.open("images/maps/" + self.map.img_file)
		img_temp = img_temp.convert("RGBA")
		img_temp = img_temp.resize((self.width, self.height), Image.ANTIALIAS)
		self.background_img = ImageTk.PhotoImage(img_temp)
		self.background = self.canvas.create_image(self.width, self.height, image = self.background_img)
		self.canvas.coords(self.background, self.width / 2, self.height / 2)
		self.canvas.tag_raise(self.car.img)

class Car:
	def __init__(self, window, game):
		self.game = game
		self.car = game.raw_car #type: cars.Car
		self.window = window #type: tk.Tk

		start_line = game.map.start
		self.x = int((start_line.x_end + start_line.x_start) / 2)
		self.y = int((start_line.y_end + start_line.y_start) / 2)
		self.speed = 0.0
		start_line_length = start_line.length()
		dot_product = start_line.x_end - start_line.x_start
		cosinus = dot_product / start_line_length
		self.start_angle = -math.acos(cosinus) + math.pi / 2
		self.angle = self.start_angle
		if start_line.y_start > start_line.y_end:
			self.angle += math.pi
		self.angle_division = self.car.maniability
		self.angle = int(self.angle_division * self.angle / math.pi) * math.pi / self.angle_division
		self.vector = self.angle_to_normalized_vector()
		self.x -= self.vector[0] * self.car.width / 2
		self.y -= self.vector[1] * self.car.height / 2
		self.canvas = game.canvas
		img_temp = Image.open("images/cars/" + self.car.img_file)
		img_temp = img_temp.convert("RGBA")
		img_temp = img_temp.resize((self.car.width, self.car.height), Image.ANTIALIAS)
		img_temp = img_temp.rotate(-self.angle * 180 / math.pi, expand = 1)
		self.img_img = ImageTk.PhotoImage(img_temp)
		self.img = self.canvas.create_image(0, 0, image = self.img_img)

		self.keys_pressed = set()
		self.paused = False
		self.lap_times = []

		self.thread = CarThread(self)
		self.thread.start()

		window.bind("<KeyPress>", lambda event : self.catch_key_press_event(event))
		window.bind("<KeyRelease>", lambda event : self.catch_key_release_event(event))
		window.bind("<FocusOut>", lambda event : self.pause())

	def angle_to_normalized_vector(self):
		return math.cos(self.angle), math.sin(self.angle)

	def catch_key_press_event(self, event):
		if self.paused:
			return

		self.keys_pressed.add(event.keysym.upper())


	def catch_key_release_event(self, event):
		if event.keysym.upper() == "ESCAPE":
			self.pause()
			return

		if event.keysym.upper() in self.keys_pressed:
			self.keys_pressed.remove(event.keysym.upper())

	def pause(self):
		if self.paused or self.thread.stopped:
			return
		self.keys_pressed.clear()
		self.paused = True

		canvas = self.canvas #type: tk.Canvas
		rectangle = canvas.create_rectangle(0, 0, self.game.width, self.game.height, fill = "#F0F0F0", stipple = "gray50")

		def resume():
			self.paused = False
			try:
				canvas.delete(rectangle)
			except:
				pass
			if resumeButton in self.game.children:
				self.game.children.remove(resumeButton)
			if quitButton in self.game.children:
				self.game.children.remove(quitButton)
			resumeButton.destroy()
			quitButton.destroy()
			self.window.unbind("<KeyRelease-Escape>", resumeId)

		def quitGame():
			self.thread.stopped = True
			self.paused = False
			mainMenu.MainMenu(self.window)

		resumeButton = tk.Button(self.window, textvariable = msgs.RESUME, font = ("Plantagenet Cherokee", 30), anchor = "center", width = 15, borderwidth = 10, bg = utils.BUTTON_BACKGROUND, relief = "groove", command = resume)
		quitButton = tk.Button(self.window, textvariable = msgs.MAIN_MENU, font = ("Plantagenet Cherokee", 30), anchor = "center", width = 15, borderwidth = 10, bg = utils.BUTTON_BACKGROUND, relief = "groove", command = quitGame)

		fc = lambda event : resume()
		resumeId = self.window.bind("<KeyRelease-Escape>", fc)

		width, height = self.game.width, self.game.height
		resumeButton.place(x = (width - resumeButton.winfo_reqwidth()) / 2, y = height / 4)
		quitButton.place(x = (width - quitButton.winfo_reqwidth()) / 2, y = height / 2)

		self.game.appendChild(resumeButton)
		self.game.appendChild(quitButton)

	def forward(self):
		self.speed = min(self.speed + self.car.acceleration, float(self.car.max_speed))

		if self.speed >= min(self.car.max_speed / 2, 10):
			AudioPlayer.playSound(AudioPlayer.DRIVING)

	def backward(self):
		self.speed = max(self.speed - self.car.acceleration, float(-self.car.max_speed / 2))

	def left(self):
		self.angle -= math.pi / self.angle_division
		self.angle %= 2 * math.pi
		if self.angle > math.pi:
			self.angle -= 2 * math.pi
		self.vector = self.angle_to_normalized_vector()
		img_temp = Image.open("images/cars/" + self.car.img_file)
		img_temp = img_temp.convert("RGBA")
		img_temp = img_temp.resize((self.car.width, self.car.height), Image.ANTIALIAS)
		img_temp = img_temp.rotate(-self.angle * 180 / math.pi, expand = 1)
		self.img_img = ImageTk.PhotoImage(img_temp)
		self.canvas.delete(self.img)
		self.img = self.canvas.create_image(self.game.width / self.game.map.width * self.x, self.game.height / self.game.map.height * self.y, image = self.img_img)

	def right(self):
		self.angle += math.pi / self.angle_division
		self.angle %= 2 * math.pi
		if self.angle > math.pi:
			self.angle -= 2 * math.pi
		self.vector = self.angle_to_normalized_vector()
		img_temp = Image.open("images/cars/" + self.car.img_file)
		img_temp = img_temp.convert("RGBA")
		img_temp = img_temp.resize((self.car.width, self.car.height), Image.ANTIALIAS)
		img_temp = img_temp.rotate(-self.angle * 180 / math.pi, expand = 1)
		self.img_img = ImageTk.PhotoImage(img_temp)
		self.canvas.delete(self.img)
		self.img = self.canvas.create_image(self.game.width / self.game.map.width * self.x, self.game.height / self.game.map.height * self.y, image = self.img_img)

class CarThread(Thread):
	def __init__(self, car):
		Thread.__init__(self)
		self.car = car
		self.stopped = False
		self.last_passage = -1
		self.last_passage_dir = 1

	def run(self):
		car = self.car
		import time
		while True:
			if car.paused:
				continue

			if self.stopped:
				return

			from utils import CONTROLS
			for key in set(car.keys_pressed):
				if key == CONTROLS["forward"]:
					car.forward()
				elif key == CONTROLS["backward"]:
					car.backward()
				elif key == CONTROLS["left"]:
					car.left()
				elif key == CONTROLS["right"]:
					car.right()
				else:
					continue

				if car.game.time == -1:
					car.game.time = 0

			newX = car.x + car.speed * car.vector[0] / 60.0
			newY = car.y + car.speed * car.vector[1] / 60.0

			collision = False
			for wall in car.game.map.walls:
				dot_product = (wall.x_end - wall.x_start) * (newX - wall.x_start) + (wall.y_end - wall.y_start) * (newY - wall.y_start)
				line = (wall.x_end - wall.x_start, wall.y_end - wall.y_start)
				line_length = math.sqrt(line[0] ** 2 + line[1] ** 2)
				xH, yH = dot_product / (line_length ** 2) * line[0] + wall.x_start, dot_product / (line_length ** 2) * line[1] + wall.y_start

				if xH < min(wall.x_start, wall.x_end) or xH > max(wall.x_start, wall.x_end) or yH < min(wall.y_start, wall.y_end) or yH > max(wall.y_start, wall.y_end):
					continue

				diagonal = math.sqrt(car.car.width ** 2 + car.car.height ** 2) / 2
				if math.sqrt((xH - newX) ** 2 + (yH - newY) ** 2) < diagonal + 0.1:
					collision = True
					break

			if collision:
				AudioPlayer.playSound(AudioPlayer.COLLISION)
				car.x = car.x - car.speed * car.vector[0] / 10.0
				car.y = car.y - car.speed * car.vector[1] / 10.0
				car.speed = -car.speed
				continue

			car.x = newX
			car.y = newY
			if CONTROLS["forward"] not in car.keys_pressed and CONTROLS["backward"] not in car.keys_pressed:
				car.speed *= 0.99
			car.canvas.coords(car.img, car.game.width / car.game.map.width * car.x, car.game.height / car.game.map.height * car.y)
			time.sleep(1.0 / 60.0)

			if car.game.time >= 0:
				car.game.time += 1.0 / 60.0
				car.game.time_label.config(text = formatTime(car.game.time))

			wall = car.game.map.start
			dot_product = (wall.x_end - wall.x_start) * (newX - wall.x_start) + (wall.y_end - wall.y_start) * (newY - wall.y_start)
			line = (wall.x_end - wall.x_start, wall.y_end - wall.y_start)
			line_length = math.sqrt(line[0] ** 2 + line[1] ** 2)
			xH, yH = dot_product / (line_length ** 2) * line[0] + wall.x_start, dot_product / (line_length ** 2) * line[1] + wall.y_start

			if xH < min(wall.x_start, wall.x_end) or xH > max(wall.x_start, wall.x_end) or yH < min(wall.y_start, wall.y_end) or yH > max(wall.y_start, wall.y_end):
				continue

			if math.sqrt((xH - newX) ** 2 + (yH - newY) ** 2) <= math.fabs(car.speed) / 10.0:
				direction = (1 if math.fabs(car.start_angle - car.angle) <= math.pi / 2 else -1) * (1 if car.speed > 0 else -1)
				if direction == self.last_passage_dir and time.time() - self.last_passage < 1:
					continue
				self.last_passage = time.time()
				self.last_passage_dir = direction

				if car.game.lap > len(car.lap_times):
					total_last_time = 0
					if car.game.lap >= 1:
						for lap in range(car.game.lap - 1):
							total_last_time += car.lap_times[lap]
					car.lap_times.append(car.game.time - total_last_time)

				if car.game.lap == car.game.map.max_laps:
					self.stopped = True
					self.end()
					return

				car.game.lap += direction
				car.game.lap_label.config(text = msgs.LAP_NUMBER.get().format(car.game.lap, car.game.map.max_laps))

	def end(self):
		car = self.car #type: Car
		canvas = car.canvas #type: tk.Canvas
		canvas.create_rectangle(0, 0, car.game.width, car.game.height, fill = "#F0F0F0", stipple = "gray50")
		canvas.create_text(car.game.window.winfo_reqwidth() / 2, car.game.window.winfo_reqheight() / 5, text = msgs.YOU_WIN.get().format(formatTime(car.game.time)), font = ("Plantagenet Cherokee", 26))
		quitButton = tk.Button(car.game.window, textvariable = msgs.MAIN_MENU, font = ("Plantagenet Cherokee", 26), bg = utils.BUTTON_BACKGROUND, command = lambda : mainMenu.MainMenu(car.game.window))
		lap_times = tk.Frame(car.game.window, borderwidth = 2, relief = tk.GROOVE)
		lap_label = tk.Label(lap_times, textvariable = msgs.LAP, font = ("Plantagenet Cherokee", 22, "bold"), width = 5)
		time_label = tk.Label(lap_times, textvariable = msgs.TIME, font = ("Plantagenet Cherokee", 22, "bold"), width = 8)
		lap_label.grid(row = 0, column = 0)
		time_label.grid(row = 0, column = 1)
		for lap in range(car.game.map.max_laps):
			lap_number = tk.Label(lap_times, text = str(lap + 1), font = ("Plantagenet Cherokee", 18))
			lap_time = tk.Label(lap_times, text = formatTime(car.lap_times[lap]), font = ("Plantagenet Cherokee", 18))
			lap_number.grid(row = lap + 1, column = 0)
			lap_time.grid(row = lap + 1, column = 1)

		quitButton.place(x = (car.game.window.winfo_reqwidth() - quitButton.winfo_reqwidth()) / 2, y = (car.game.window.winfo_reqheight() - quitButton.winfo_reqheight()) / 2)
		lap_times.place(x = car.game.window.winfo_reqwidth() - lap_times.winfo_reqwidth(), y = car.game.window.winfo_reqheight() / 5)

		car.game.appendChild(quitButton)
		car.game.appendChild(lap_times)

def formatTime(t: float):
	hours = int(t // 3600)
	t %= 3600
	minutes = int(t // 60)
	t %= 60
	seconds = int(t)
	t %= 1
	millis = int(1000 * t)
	return str(hours).zfill(2) + ":" + str(minutes).zfill(2) + ":" + str(seconds).zfill(2) + "." + str(millis).zfill(3)
