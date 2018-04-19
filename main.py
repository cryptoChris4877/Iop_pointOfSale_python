#!/usr/bin/env python
import threading
import Queue
import iop

p= iop.POS()
mainT= threading.Thread(target=p.startLoop)
guiT= threading.Thread(target=p.handleGuiUpdate)
mainT.daemon = True # kills all threads with ctrl-c
guiT.daemon = True # kills all threads with ctrl-c
mainT.start()
guiT.start()
p.gui.mainloop()