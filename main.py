#-------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label object bboxes for ImageNet Detection data
# Author:      Qiushi
# Created:     06/06/2014

#
#-------------------------------------------------------------------------------
from __future__ import division
from Tkinter import *
import tkMessageBox
from PIL import Image, ImageTk
import os
import glob
import random

# colors for the bboxes
COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']
# image sizes for the examples
SIZE = 256, 256

class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("LabelTool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width = FALSE, height = FALSE)

        # initialize global state
        self.imageDir = ''
        self.imageList= []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 1#already loaded it as 1,cuz thats what im using
        self.imagename = ''
        self.labelfilename = ''
        self.tkimg = None

        self.label_number_map = ["","Car","2 wheeler","Bus","Truck","Auto"]
        self.reverse_label_map = {"":0,"Car":1,"2 wheeler":2,"Bus":3,"Truck":4,"Auto":5}

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None
        self.bbox_labels_list = []

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.label = Label(self.frame, text = "Image Dir:")
        self.label.grid(row = 0, column = 0, sticky = E)
        self.entry = Entry(self.frame)
        self.entry.grid(row = 0, column = 1, sticky = W+E)
        self.ldBtn = Button(self.frame, text = "Load", command = self.loadDir)
        self.ldBtn.grid(row = 0, column = 2, sticky = W+E)
        self.label_1_Btn = Button(self.frame, text = "Car(1)",width = 16,command = self.addLabel1)
        self.label_1_Btn.grid(row = 0, column = 3, sticky = N+E)
        self.label_2_Btn = Button(self.frame, text = "2 Wheeler(2)",width = 16,command = self.addLabel2)
        self.label_2_Btn.grid(row = 0, column = 4, sticky = N+E)
        self.label_3_Btn = Button(self.frame, text = "Bus(3)",width = 16,command = self.addLabel3)
        self.label_3_Btn.grid(row = 1, column = 3, sticky = N+E)
        self.label_4_Btn = Button(self.frame, text = "Truck(4)",width = 16,command = self.addLabel4)
        self.label_4_Btn.grid(row = 1, column = 4, sticky = N+E)
        self.label_5_Btn = Button(self.frame, text = "Auto(5)",width = 16,command = self.addLabel5)
        self.label_5_Btn.grid(row = 2, column = 3, sticky = N+E)
        #these seem like names given here and probably no initialization is needed since these names don't appear anywhere else
        #columns are just 0,1,2

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)  # press <Espace> to cancel current bbox
        self.parent.bind("1",self.addLabel1)
        self.parent.bind("2",self.addLabel2)
        self.parent.bind("3",self.addLabel3)
        self.parent.bind("4",self.addLabel4)
        self.parent.bind("5",self.addLabel5)
        self.parent.bind("s", self.cancelBBox)
        self.parent.bind("a", self.prevImage) # press 'a' to go backforward
        # self.parent.bind("<space>", self.nextImage) # press ' ' to go forward
        self.parent.bind("<Button-3>", self.nextImage) # right click to go forward
        self.mainPanel.grid(row = 1, column = 1, rowspan = 4, sticky = W+N)

        # self.parent.bind("1", self.addLabel1)
        #here opened the main panel and bound certain keys(inputs) to certain functions defined later
        #bind keys to classes here

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text = 'Bounding boxes:')
        self.lb1.grid(row = 1, column = 2,  sticky = W+N)
        self.listbox = Listbox(self.frame, width = 22, height = 12)
        self.listbox.grid(row = 2, column = 2, sticky = N)
        self.btnDel = Button(self.frame, text = 'Delete', command = self.delBBox)
        self.btnDel.grid(row = 3, column = 2, sticky = W+E+N)
        self.btnClear = Button(self.frame, text = 'ClearAll', command = self.clearBBox)
        self.btnClear.grid(row = 4, column = 2, sticky = W+E+N)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row = 5, column = 1, columnspan = 2, sticky = W+E)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev', width = 10, command = self.prevImage)
        self.prevBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>', width = 10, command = self.nextImage)
        self.nextBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.progLabel = Label(self.ctrPanel, text = "Progress:     /    ")
        self.progLabel.pack(side = LEFT, padx = 5)
        self.tmpLabel = Label(self.ctrPanel, text = "Go to Image No.")
        self.tmpLabel.pack(side = LEFT, padx = 5)
        self.idxEntry = Entry(self.ctrPanel, width = 5)
        self.idxEntry.pack(side = LEFT)
        self.goBtn = Button(self.ctrPanel, text = 'Go', command = self.gotoImage)
        self.goBtn.pack(side = LEFT)

        # example pannel for illustration
        self.egPanel = Frame(self.frame, border = 10)
        self.egPanel.grid(row = 1, column = 0, rowspan = 5, sticky = N)
        self.tmpLabel2 = Label(self.egPanel, text = "Examples:")
        self.tmpLabel2.pack(side = TOP, pady = 5)
        self.egLabels = []
        for i in range(3):
            self.egLabels.append(Label(self.egPanel))
            self.egLabels[-1].pack(side = TOP)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = RIGHT)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(4, weight = 1)

        # for debugging
##        self.setImage()
##        self.loadDir()

    def loadDir(self, dbg = False):
        if not dbg:
            s = self.entry.get()
            self.parent.focus()
            self.category = int(s)
        else:
            s = r'D:\workspace\python\labelGUI'
##        if not os.path.isdir(s):
##            tkMessageBox.showerror("Error!", message = "The specified dir doesn't exist!")
##            return
        # get image list
        self.imageDir = os.path.join(r'./Images', '%03d' %(self.category))
        self.imageList = sorted(glob.glob(os.path.join(self.imageDir, '*.jpg')))
        print "imageList =",self.imageList
        if len(self.imageList) == 0:
            print 'No .JPEG images found in the specified dir!'
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

         # set up output dir
        self.outDir = os.path.join(r'./Labels', '%03d' %(self.category))
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)

        # load example bboxes
        self.egDir = os.path.join(r'./Examples', '%03d' %(self.category))
        if not os.path.exists(self.egDir):
            return
        filelist = glob.glob(os.path.join(self.egDir, '*.jpg'))
        self.tmp = []
        self.egList = []
        #random.shuffle(filelist)
        print "filelist =",filelist
        for (i, f) in enumerate(filelist):
        	print "in the loop"
        	if i == 3:
        		print "breing the loop"
        		break
        	im = Image.open(f)
        	print im
        	r = min(SIZE[0] / im.size[0], SIZE[1] / im.size[1])
        	new_size = int(r * im.size[0]), int(r * im.size[1])
        	self.tmp.append(im.resize(new_size, Image.ANTIALIAS))
        	self.egList.append(ImageTk.PhotoImage(self.tmp[-1]))
        	self.egLabels[i].config(image = self.egList[-1], width = SIZE[0], height = SIZE[1])

        self.loadImage()
        print '%d images loaded from %s' %(self.total, s)

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        self.img = (Image.open(imagepath)).resize((960,675))#2,1.6
        self.tkimg = ImageTk.PhotoImage(self.img)
        self.mainPanel.config(width = max(self.tkimg.width(), 400), height = max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.progLabel.config(text = "%04d/%04d" %(self.cur, self.total))

        # load labels
        self.clearBBox()
        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.outDir, labelname)
        bbox_cnt = 0
        loaded_label_str = ""
        loaded_label_num = 0
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as f:
                for (i, line) in enumerate(f):
                    if i == 0:
                        bbox_cnt = int(line.strip())
                        continue
                    elif i%2 == 1: #odd lines contain the label
                        loaded_label_str = str(line.strip())
                        loaded_label_num = self.reverse_label_map[loaded_label_str]

                    else:
                        tmp = [int(t.strip()) for t in line.split()]
                        tmp = [int(tmp[0]/2),int(tmp[1]/1.6),int(tmp[2]/2),int(tmp[3]/1.6)]
    ##                    print tmp
                        self.bboxList.append(tuple(tmp))
                        self.bbox_labels_list.append(loaded_label_num)
                        tmpId = self.mainPanel.create_rectangle(tmp[0], tmp[1], \
                                                                tmp[2], tmp[3], \
                                                                width = 2, \
                                                                outline = COLORS[(len(self.bboxList)-1) % len(COLORS)])
                        self.bboxIdList.append(tmpId)
                        self.listbox.insert(END, '(%d, %d) -> (%d, %d) : %d' %(tmp[0], tmp[1], tmp[2], tmp[3],loaded_label_num))
                        self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])


    def saveImage(self):
        with open(self.labelfilename, 'w') as f:
            f.write('%d\n' %len(self.bboxList))
            for i in range(len(self.bboxList)):
                bbox = self.bboxList[i]
                bbox = (bbox[0]*2,int(bbox[1]*1.6),bbox[2]*2,int(bbox[3]*1.6))

                print "i =",i
                f.write(self.label_number_map[self.bbox_labels_list[i]] + '\n')

                f.write(' '.join(map(str, bbox)) + '\n')
        print 'Image No. %d saved' %(self.cur)


    def mouseClick(self, event):
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            self.bboxList.append((x1, y1, x2, y2))

            self.bbox_labels_list.append(0)  #since no label assigned till now.do that in the button action

            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '(%d, %d) -> (%d, %d) : %d' %(x1, y1, x2, y2,0)) #the last one is the class of the label assigned
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

        self.STATE['click'] = 1 - self.STATE['click']

    def mouseMove(self, event):
        self.disp.config(text = 'x: %d, y: %d' %(event.x, event.y))
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width = 2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width = 2)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                            event.x, event.y, \
                                                            width = 2, \
                                                            outline = COLORS[len(self.bboxList) % len(COLORS)])

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.bbox_labels_list.pop(idx)
        self.listbox.delete(idx)

    def addLabel1(self,event = None):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return

        #edit the label and what comes in the box
        idx = int(sel[0])
        self.bbox_labels_list[idx] = 1

        temp = self.bboxList[idx]
        self.listbox.delete(idx)
        self.listbox.insert(idx, '(%d, %d) -> (%d, %d) : %d' %(temp[0],temp[1],temp[2],temp[3],1))
        self.listbox.itemconfig(idx,fg = COLORS[(idx) % len(COLORS)])

    def addLabel2(self,event = None):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return

        #edit the label and what comes in the box
        idx = int(sel[0])
        self.bbox_labels_list[idx] = 2

        temp = self.bboxList[idx]
        self.listbox.delete(idx)
        self.listbox.insert(idx, '(%d, %d) -> (%d, %d) : %d' %(temp[0],temp[1],temp[2],temp[3],2))
        self.listbox.itemconfig(idx,fg = COLORS[(idx) % len(COLORS)])

    def addLabel3(self,event = None):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return

        #edit the label and what comes in the box
        idx = int(sel[0])
        self.bbox_labels_list[idx] = 3

        temp = self.bboxList[idx]
        self.listbox.delete(idx)
        self.listbox.insert(idx, '(%d, %d) -> (%d, %d) : %d' %(temp[0],temp[1],temp[2],temp[3],3))
        self.listbox.itemconfig(idx,fg = COLORS[(idx) % len(COLORS)])

    def addLabel4(self,event = None):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return

        #edit the label and what comes in the box
        idx = int(sel[0])
        self.bbox_labels_list[idx] = 4

        temp = self.bboxList[idx]
        self.listbox.delete(idx)
        self.listbox.insert(idx, '(%d, %d) -> (%d, %d) : %d' %(temp[0],temp[1],temp[2],temp[3],4))
        self.listbox.itemconfig(idx,fg = COLORS[(idx) % len(COLORS)])

    def addLabel5(self,event = None):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return

        #edit the label and what comes in the box
        idx = int(sel[0])
        self.bbox_labels_list[idx] = 5

        temp = self.bboxList[idx]
        self.listbox.delete(idx)
        self.listbox.insert(idx, '(%d, %d) -> (%d, %d) : %d' %(temp[0],temp[1],temp[2],temp[3],5))
        self.listbox.itemconfig(idx,fg = COLORS[(idx) % len(COLORS)])

    #too much repeated code. make this neater

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []
        self.bbox_labels_list = []

    def prevImage(self, event = None):
        self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event = None):
        self.saveImage()
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()

    def gotoImage(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()

##    def setImage(self, imagepath = r'test2.png'):
##        self.img = Image.open(imagepath)
##        self.tkimg = ImageTk.PhotoImage(self.img)
##        self.mainPanel.config(width = self.tkimg.width())
##        self.mainPanel.config(height = self.tkimg.height())
##        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)

if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.resizable(width =  True, height = True)
    root.mainloop()
