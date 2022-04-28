import unittest
from xml.etree import ElementTree
from os import path
import cv2
import pytesseract
import re
import sys


def get_power_toughness(data):
	data = data.translate(str.maketrans('', '', ' \n\t\r')).replace("L", "1").replace("O", "0").replace("o", "0")
	data = re.sub(r'[\x0c]+','', data)
	if bool(re.match(r'^[0-9/*]+$', data)) and "/" in data:
		power, toughness = data.split("/")[0], data.split("/")[1]
		if int(power) > 20 or int(toughness) > 20:
			raise ValueError("Bad data")
		return power, toughness
	else:
		raise ValueError("Bad data")

class TestXML(unittest.TestCase):

	def setUp(self):
		if sys.platform.startswith('win'):
			pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
		try:
			dom = ElementTree.parse("./data/customsets/tumbled-mtg-cards.xml")
			cards = dom.find('cards')
			self.cards = cards.findall('card')
			dom = ElementTree.parse("./data/tokens.xml")
			cards = dom.find('cards')
			self.tokens = cards.findall('card')
		except:
			self.assertTrue(False, "The XML is invalid, you missed a < or > or something.")


	def test_cards_have_image(self):
		self.assertGreater(len(self.cards), 0, "No cards in XML... apparently")
		for card in self.cards + self.tokens:
			name = card.find('name').text
			image = f"./data/pics/CUSTOM/{name}.png"
			self.assertTrue(path.isfile(image), f'Cannot find an image for card {image}')
			if card.find("related") is not None:
				name = card.find('related').text
				image = f"./data/pics/CUSTOM/{name}.png"
				self.assertTrue(path.isfile(image), f'Cannot find an image for RELATED card {image}')

	
	def test_power_toughness(self):
		for card in self.cards + self.tokens:
			name = card.find('name').text
			if(card.find('pt') is not None):
				power = card.find('pt').text.split("/")[0]
				toughness = card.find('pt').text.split("/")[1]
				image = f"./data/pics/CUSTOM/{name}.png"
				if not path.isfile(image):
					continue
				image = cv2.imread(image, 0)
				image = cv2.resize(image,(0,0),fx=7,fy=7)
				thresh = 255 - cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
				x,y,w,h = 298*7, 473*7, 36*7, 19*7  
				ROI = thresh[y:y+h,x:x+w]
				data = pytesseract.image_to_string(ROI, lang='eng',config='--psm 6')
				try:
					p, t = get_power_toughness(data)
				except Exception as e:
					continue
				self.assertEqual(power, p, f"XML power {power} does not equal card power {p} for card {name}")
				self.assertEqual(toughness, t, f"XML toughness {toughness} does not equal card toughness {t} for card {name}")

if __name__ == '__main__':
	unittest.main()