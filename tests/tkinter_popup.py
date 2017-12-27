import tkinter as tk
import urllib.request, time
from PIL import ImageTk, Image
import threading

#TODO: add to config
window_width = 350
window_height = 100
padx = 0
pady = 100

class Popup():
	def show(self):
		#init window
		self.root = tk.Tk()
		self.root.title('Pyxis')
		self.root.configure(background='white')
		self.root.attributes('-topmost', 'true')
		xpos = self.root.winfo_screenwidth() - window_width - padx
		ypos = self.root.winfo_screenheight() - window_height - pady
		g = ('%sx%s+%s+%s' % (window_width, window_height, xpos, ypos))
		self.root.geometry(g)
		
		#create a canvas
		cv = tk.Canvas(bg='white', width=100, height=100, highlightthickness=0)
		cv.grid(row=0, column=0, rowspan=3, sticky='w')
		
		#album img
		img_url = 'http://cont-2.p-cdn.com/images/public/rovi/albumart/8/2/3/1/5099993481328_500W_500H.jpg'
		img_raw = urllib.request.urlopen(img_url)
		img_interm = Image.open(img_raw)
		img_interm.thumbnail((100,100))
		img = ImageTk.PhotoImage(img_interm)
		
		#place image on canvas
		cv.create_image(0, 0, image=img, anchor='nw')
		
		#labels
		label = tk.Label(text='#Songname').grid(row=0, sticky='w', column=1)
		label = tk.Label(text='#Artist - #Album').grid(row=1, sticky='w', column=1)
		label = tk.Label(text='-').grid(row=2, sticky='w', column=1)
		
		#remove top bar
		self.root.overrideredirect(1)
		
		#TODO: rewrite this bit
		#wait 5 seconds and hide the window
		self.root.update()
		self.root.deiconify()
		self.root.after(5000, self.root.quit())
		#self.root.mainloop()
		
test = Popup()
t = threading.Thread(target=test.show)
t.start()