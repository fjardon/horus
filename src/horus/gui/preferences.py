#!/usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------#
#                                                                       #
# This file is part of the Horus Project                                #
#                                                                       #
# Copyright (C) 2014-2015 Mundo Reader S.L.                             #
#                                                                       #
# Date: June, November 2014                                             #
# Author: Jesús Arroyo Torrens <jesus.arroyo@bq.com>                    #
#                                                                       #
# This program is free software: you can redistribute it and/or modify  #
# it under the terms of the GNU General Public License as published by  #
# the Free Software Foundation, either version 2 of the License, or     #
# (at your option) any later version.                                   #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          #
# GNU General Public License for more details.                          #
#                                                                       #
# You should have received a copy of the GNU General Public License     #
# along with this program. If not, see <http://www.gnu.org/licenses/>.  #
#                                                                       #
#-----------------------------------------------------------------------#

__author__ = "Jesús Arroyo Torrens <jesus.arroyo@bq.com>"
__license__ = "GNU General Public License v2 http://www.gnu.org/licenses/gpl.html"

import wx._core
import select
import threading

from horus.util import profile, resources, system as sys
from horus.util.avrHelpers import AvrDude


class PreferencesDialog(wx.Dialog):
	def __init__(self, parent):
		super(PreferencesDialog, self).__init__(None, title=_("Preferences"))

		self.main = parent

		#-- Graphic elements
		self.conParamsStaticText = wx.StaticText(self, label=_("Connection Parameters"), style=wx.ALIGN_CENTRE)
		self.serialNameLabel = wx.StaticText(self, label=_("Serial Name"))
		self.serialNames = self.main.serialList()
		self.serialNameCombo = wx.ComboBox(self, choices=self.serialNames, size=(170,-1))
		self.baudRateLabel = wx.StaticText(self, label=_("Baud Rate"))
		self.baudRates = self.main.baudRateList()
		self.baudRateCombo = wx.ComboBox(self, choices=self.baudRates, size=(172,-1), style=wx.CB_READONLY)
		self.cameraIdLabel = wx.StaticText(self, label=_("Camera Id"))
		self.cameraIdNames = self.main.videoList()
		self.cameraIdCombo = wx.ComboBox(self, choices=self.cameraIdNames, size=(167,-1), style=wx.CB_READONLY)

		self.firmwareStaticText = wx.StaticText(self, label=_("Burn Firmware"), style=wx.ALIGN_CENTRE)
		self.boardLabel = wx.StaticText(self, label=_("AVR Board"))
		self.boards = profile.getProfileSettingObject('board').getType()
		board = profile.getProfileSetting('board')
		self.boardsCombo = wx.ComboBox(self, choices=self.boards, value=board , size=(168,-1), style=wx.CB_READONLY)
		self.hexLabel = wx.StaticText(self, label=_("Binary file"))
		self.hexCombo = wx.ComboBox(self, choices=[_("Default"), _("External file...")], value=_("Default") , size=(172,-1), style=wx.CB_READONLY)
		self.clearCheckBox = wx.CheckBox(self, label=_("Clear EEPROM"))
		self.uploadFirmwareButton = wx.Button(self, label=_("Upload Firmware"))
		self.gauge = wx.Gauge(self, range=100, size=(180, 30))
		self.gauge.Hide()

		self.languageLabel = wx.StaticText(self, label=_("Language"))
		self.languages = [row[1] for row in resources.getLanguageOptions()]
		self.languageCombo = wx.ComboBox(self, choices=self.languages, value=profile.getPreference('language') , size=(175,-1), style=wx.CB_READONLY)

		invert = profile.getProfileSettingBool('invert_motor')
		self.invertMotorCheckBox = wx.CheckBox(self, label=_("Invert the motor direction"))
		self.invertMotorCheckBox.SetValue(invert)

		self.okButton = wx.Button(self, label=_("Ok"))

		#-- Events
		self.serialNameCombo.Bind(wx.EVT_TEXT, self.onSerialNameComboChanged)
		self.serialNameCombo.Bind(wx.EVT_COMBOBOX, self.onSerialNameComboChanged)
		self.baudRateCombo.Bind(wx.EVT_COMBOBOX, self.onBaudRateComboChanged)
		self.cameraIdCombo.Bind(wx.EVT_COMBOBOX, self.onCameraIdComboChanged)
		self.boardsCombo.Bind(wx.EVT_COMBOBOX, self.onBoardsComboChanged)
		self.hexCombo.Bind(wx.EVT_COMBOBOX, self.onHexComboChanged)
		self.uploadFirmwareButton.Bind(wx.EVT_BUTTON, self.onUploadFirmware)
		self.languageCombo.Bind(wx.EVT_COMBOBOX, self.onLanguageComboChanged)
		self.invertMotorCheckBox.Bind(wx.EVT_CHECKBOX, self.onInvertMotor)
		self.okButton.Bind(wx.EVT_BUTTON, self.onClose)
		self.Bind(wx.EVT_CLOSE, self.onClose)

		#-- Fill data
		currentSerial = profile.getProfileSetting('serial_name')
		if len(self.serialNames) > 0:
			if currentSerial not in self.serialNames:
				self.serialNameCombo.SetValue(self.serialNames[0])
			else:
				self.serialNameCombo.SetValue(currentSerial)

		currentBaudRate = profile.getProfileSetting('baud_rate')
		self.baudRateCombo.SetValue(currentBaudRate)

		currentVideoId = profile.getProfileSetting('camera_id')
		if len(self.cameraIdNames) > 0:
			if currentVideoId not in self.cameraIdNames:
				self.cameraIdCombo.SetValue(self.cameraIdNames[0])
			else:
				self.cameraIdCombo.SetValue(currentVideoId)		

		#-- Call Events
		self.onSerialNameComboChanged(None)
		self.onCameraIdComboChanged(None)

		#-- Layout
		vbox = wx.BoxSizer(wx.VERTICAL)
		    
		vbox.Add(self.conParamsStaticText, 0, wx.ALL, 10)
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(self.serialNameLabel, 0, wx.ALL^wx.RIGHT, 10)
		hbox.Add(self.serialNameCombo, 0, wx.ALL, 5)
		vbox.Add(hbox)
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(self.baudRateLabel, 0, wx.ALL, 10)
		hbox.Add(self.baudRateCombo, 0, wx.ALL, 5)
		vbox.Add(hbox)
		hbox = wx.BoxSizer(wx.HORIZONTAL)   
		hbox.Add(self.cameraIdLabel, 0, wx.ALL, 10)
		hbox.Add(self.cameraIdCombo, 0, wx.ALL, 5)
		vbox.Add(hbox)

		vbox.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)

		vbox.Add(self.firmwareStaticText, 0, wx.ALL, 10)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(self.boardLabel, 0, wx.ALL, 10)
		hbox.Add(self.boardsCombo, 0, wx.ALL, 5)
		vbox.Add(hbox)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(self.hexLabel, 0, wx.ALL, 10)
		hbox.Add(self.hexCombo, 0, wx.ALL, 5)
		vbox.Add(hbox)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(self.uploadFirmwareButton, 0, wx.ALL, 10)
		hbox.Add(self.clearCheckBox, 0, wx.ALL^wx.LEFT, 15)
		vbox.Add(hbox)

		vbox.Add(self.gauge, 0, wx.EXPAND|wx.ALL^wx.TOP, 10)

		vbox.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL^wx.TOP, 5)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(self.languageLabel, 0, wx.ALL, 10)
		hbox.Add(self.languageCombo, 0, wx.ALL, 5)
		vbox.Add(hbox)

		vbox.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(self.invertMotorCheckBox, 0, wx.ALL, 15)
		vbox.Add(hbox)

		vbox.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)

		vbox.Add(self.okButton, 0, wx.ALL|wx.EXPAND, 10)

		self.hexPath = None

		self.SetSizer(vbox)
		self.Centre()

		self.Fit()

	def onClose(self, event):
		self.EndModal(wx.ID_OK)
		self.Destroy()
	

	def onSerialNameComboChanged(self, event):
		if len(self.serialNameCombo.GetValue()):
			profile.putProfileSetting('serial_name', self.serialNameCombo.GetValue())

	def onBaudRateComboChanged(self, event):
		if self.baudRateCombo.GetValue() in self.baudRates:
			profile.putProfileSetting('baud_rate', int(self.baudRateCombo.GetValue()))

	def onCameraIdComboChanged(self, event):
		if len(self.cameraIdCombo.GetValue()):
			profile.putProfileSetting('camera_id', self.cameraIdCombo.GetValue())

	def onBoardsComboChanged(self, event):
		profile.putProfileSetting('board', self.boardsCombo.GetValue())

	def onHexComboChanged(self, event):
		value = self.hexCombo.GetValue()
		if value == _("Default"):
			self.hexPath = None
		elif value == _("External file..."):
			dlg = wx.FileDialog(self, _("Select binary file to load"), style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
			dlg.SetWildcard("hex files (*.hex)|*.hex")
			if dlg.ShowModal() == wx.ID_OK:
				self.hexPath = dlg.GetPath()
				self.hexCombo.SetValue(dlg.GetFilename())
			dlg.Destroy()

	def onUploadFirmware(self, event):
		if self.serialNameCombo.GetValue() != '':
			self.beforeLoadFirmware()
			baudRate = self._getBaudRate(self.boardsCombo.GetValue())
			clearEEPROM = self.clearCheckBox.GetValue()
			threading.Thread(target=self.loadFirmware, args=(baudRate,clearEEPROM)).start()

	def _getBaudRate(self, value):
		if value == 'Arduino Uno':
			return 115200
		elif value == 'BT ATmega328':
			return 19200

	def loadFirmware(self, hexBaudRate, clearEEPROM):
		avr_dude = AvrDude(port=profile.getProfileSetting('serial_name'), baudRate=hexBaudRate)
		extraFlags = []
		if clearEEPROM:
			extraFlags = ["-D"]
		proc = avr_dude.flash(extraFlags=extraFlags, hexPath=self.hexPath) #TODO: fails if change board
		count = -50
		while count < 100:
			if proc:
				readx = select.select([proc.stderr.fileno()], [], [])[0]
				if readx:
					out = proc.stderr.read()
					if 'not in sync' in out or 'Invalid' in out:
						wx.CallAfter(self.wrongBoardMessage)
						break
					count += out.count('#')
					if count >= 0:
						self.gauge.SetValue(count)
				else:
					break
		wx.CallAfter(self.afterLoadFirmware)

	def wrongBoardMessage(self):
		dlg = wx.MessageDialog(self, _("Probably you have selected the wrong board. Select other Board"), 'Wrong Board', wx.OK|wx.ICON_ERROR)
		dlg.ShowModal()
		dlg.Destroy()

	def beforeLoadFirmware(self):
		self.uploadFirmwareButton.Disable()
		self.clearCheckBox.Disable()
		self.boardsCombo.Disable()
		self.okButton.Disable()
		if not sys.isWindows():
			self.gauge.SetValue(0)
			self.gauge.Show()
		self.waitCursor = wx.BusyCursor()
		self.Centre()
		self.Fit()
		self.Layout()

	def afterLoadFirmware(self):
		self.uploadFirmwareButton.Enable()
		self.clearCheckBox.Enable()
		self.boardsCombo.Enable()
		self.okButton.Enable()
		if not sys.isWindows():
			self.gauge.Hide()
		del self.waitCursor
		self.Fit()
		self.Layout()

	def onLanguageComboChanged(self, event):
		if profile.getPreference('language') is not self.languageCombo.GetValue():
			profile.putPreference('language', self.languageCombo.GetValue())
			wx.MessageBox(_("You have to restart the application to make the changes effective."), 'Info', wx.OK | wx.ICON_INFORMATION)

	def onInvertMotor(self, event):
		profile.putProfileSetting('invert_motor', self.invertMotorCheckBox.GetValue())