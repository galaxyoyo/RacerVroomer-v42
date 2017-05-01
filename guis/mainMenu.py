#coding: utf-8

import tkinter as tk
import os
# Import messages vars
import messages as msgs
import utils
from . import GUI, settings, playerMode

class MainMenu(GUI):
	def __init__(self, window):
		GUI.__init__(self)

		def on_closing():
			os._exit(0) # Force closing process, killing all threads

		window.protocol("WM_DELETE_WINDOW", on_closing)


		onePlayerMode = tk.Button(window, textvariable = msgs.SINGLE_PLAYER, font = ("Plantagenet Cherokee", 30), anchor = "center", width = 15, borderwidth = 10, bg = utils.BUTTON_BACKGROUND, relief = "groove", command = lambda  : playerMode.SinglePlayer(window))
		multiplayer = tk.Button(window, textvariable = msgs.MULTI_PLAYER, font = ("Plantagenet Cherokee", 30), anchor = "center", width = 15, borderwidth = 10, bg = utils.BUTTON_BACKGROUND, relief = "groove", command = lambda : playerMode.MultiPlayer(window))
		options = tk.Button(window, textvariable = msgs.SETTINGS, font = ("Plantagenet Cherokee", 30), anchor = "center", width = 15, borderwidth = 10, bg = utils.BUTTON_BACKGROUND, relief = "groove", command = lambda : settings.Settings(window))
		quitGame = tk.Button(window, textvariable = msgs.QUIT, font = ("Plantagenet Cherokee", 30), anchor = "center", width = 15, borderwidth = 10, bg = utils.BUTTON_BACKGROUND, relief = "groove", command = on_closing)

		onePlayerMode.grid(row = 2,column = 0)
		multiplayer.grid(row=2,column = 1)
		options.grid(row = 2,column = 2)
		quitGame.grid(row = 2,column = 3)

		self.appendChild(onePlayerMode)
		self.appendChild(multiplayer)
		self.appendChild(options)
		self.appendChild(quitGame)
