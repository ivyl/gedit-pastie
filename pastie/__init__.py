from gettext import gettext as _

import gtk, gtk.glade
import pygtk
pygtk.require('2.0')
import gedit
import os
import pastie
import windows

#pice of XML, it tells where to place our action
ui_str = """<ui>
  <menubar name="MenuBar">
    <menu name="ToolsMenu" action="Tools">
      <placeholder name="ToolsOps_2">
         <menuitem name="Pastie" action="Pastie"/>
         <menuitem name="PastieDefault" action="PastieDefault" />
      </placeholder>
    </menu>
  </menubar>
</ui>
"""


#WINDOW HEPER
class PastieWindowHelper:

    #ACTIONS
    
    def __init__(self, plugin, window):
        self._window = window
        self._plugin = plugin
        self.pastie_window = windows.PastieWindow()
        self.pastie_window.get_text = self.get_selected_text
        self._insert_menu() #insert menu item

        
    def deactivate(self):
        self._remove_menu() #remove installed menu items
        self._window = None
        self._plugin = None
        
    def update_ui(self):
        #called whenever this window has been updated (active, change, etc)
        self._action_group.set_sensitive(self._window.get_active_document() != None)

    #MENU INSERTION
        
    def _insert_menu(self):
        manager = self._window.get_ui_manager() #get the GtkUIManager
        self._action_group = gtk.ActionGroup("PastieActions") #new group
        #menu position (from ui_str) and ctrl + shift + d shourtcut fo pastie action
        self._action_group.add_actions([("Pastie", None, _("Pastie selection"),
                                         '<Control><Shift>d', _("Pastie selection"),
                                         self.pastie_window.show)])
        self._action_group.add_actions([("PastieDefault", None, _("Pastie with defaults"),
                                         '<Control><Shift>c', _("Pastie with defaults"),
                                         self.pastie_window.paste_defaults)])                                 
        manager.insert_action_group(self._action_group, -1) 
        self._ui_id = manager.add_ui_from_string(ui_str)
       
    def _remove_menu(self):
        "removes elements form menu which plugin adds"
        manager = self._window.get_ui_manager()
        manager.remove_ui(self._ui_id) #_ui_id is stored id of added menu
        manager.remove_action_group(self._action_group) #removes action group
        manager.ensure_update()
    
    
    #METHODS
    
    def get_selected_text(self):
        "gets selected text form current document and returns it"
        doc = self._window.get_active_document()
        
        if not doc: 
            return None
        if doc.get_has_selection():
            start, end = doc.get_selection_bounds()
        else: 
            return None  
        
        return doc.get_text(start,end)
        
    #MENU
        
    def on_pastie_activate(self, action):
        "activates when we choose to pastie selection"
        self._pastie_window.show()
        self._pastie_glade.get_widget("ok_button").grab_focus()
        
    def on_pastie_defaults_activate(self, action):
        pass
    
    
    #GLADE WRAPPER
    
    def _init_glade_paste_window(self):
        "inits paste window from glade file and sets actions"
        self._pastie_glade = gtk.glade.XML( os.path.dirname( __file__ ) + "/PasteWindow.glade" )
        self._pastie_window = self._pastie_glade.get_widget("PastieWindow")
        self._pastie_window.connect("delete_event", self._hide)
       
        for lang in pastie.LANGS:
            self._pastie_glade.get_widget("syntax").append_text(lang)
        
        self._pastie_glade.get_widget("syntax").set_active(0) #sets active posision in syntax list
        
        self._pastie_glade.get_widget("ok_button").connect("clicked", self._ok_button_clicked)
        self._pastie_glade.get_widget("cancel_button").connect("clicked", lambda a: self._pastie_window.hide())
    
       
    def _init_glade_inform_window(self):
        self._inform_glade = gtk.glade.XML( os.path.dirname( __file__ ) + "/Inform.glade" )
        self._inform_window = self._inform_glade.get_widget("InformWindow")
        self._inform_window.connect("delete_event", self._hide)
        self._inform_glade.get_widget("ok_button").connect("clicked", lambda a: self._inform_window.hide())
        
        
    #GTK ACTIONS
    
    def _ok_button_clicked(self, buttin):
        "respond to clicking ok button in paste window"
        combox = self._pastie_glade.get_widget("syntax")
        model = combox.get_model()
        active = combox.get_active()
        syntax = model[active][0]
        priv = self._pastie_glade.get_widget("private").get_active()
        self._pastie_window.hide()
        self._paste(syntax, priv)
    
    def _hide(self, widget, event):
        widget.hide()
        return True
        
    #PASTE ACTIONS
    
    def _paste(self, syntax, priv):
        "pastes selected text and displays window with link"
        p = pastie.Pastie(self.get_selected_text(), syntax, priv)
        entry = self._inform_glade.get_widget("link") #gets TextEntry field from inform window
        entry.set_text("please wait")
        self._inform_window.show() #shows window
        entry.set_text(p.paste())
        
    def _paste_clipbord(self, syntax, priv):
        "pastes selected text and copys link to clipboard"
        clipboard = gtk.clipboard_get('CLIPBOARD')
        p = pastie.Pastie(self.get_selected_text(), syntax, priv)
        clipboard.set_text(p.paste())
        clipboard.store()

#PLUGIN
class PastiePlugin(gedit.Plugin):
    def __init__(self):
        gedit.Plugin.__init__(self)
        
    def activate(self, window):
        self._instances = PastieWindowHelper(self, window)
        
    def deactivate(self, window):
        self._instances.deactivate()
        del self._instances
        
    def update_ui(self, window):
        self._instances.update_ui()
    
    def is_configurable(self):
        return True
    
    def create_configure_dialog(self):
        return self._instances.pastie_window.config.window.window
