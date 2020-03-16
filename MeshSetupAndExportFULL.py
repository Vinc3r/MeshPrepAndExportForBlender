# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


bl_info = { # THIS .PY FILE WILL BE SPLIT INTO 3 SEPARATE .PY FILES IN THE RELEASE VERSION
    "name":"Mesh Setup / Export Tool",
    "author":"Ethan Simon-Law",
    "version":(0,8),
    "blender":(2, 82, 7),
    "location":"Sidebar, Scene Properties",
    "warning":"This is a beta version of the software",
    "desctiption":"A tool made to help prepare your mesh for export and export swiftly with a single click or shortcut press",
    "wiki_url": "https://gdoc.pub/doc/e/2PACX-1vSIqOGhZuRAH_DQdCsRli4KoZGF-ngviGYuSTO0U_twBs6mg6D2DpXuiGIy9k1IMIDp4KQDxQ_MWI5x",
    "category":"3D View"}


                    # IMPORT LIBRARIES


import bpy
import os
import rna_keymap_ui
from bpy.types import (Panel, Operator, PropertyGroup, AddonPreferences)
from bpy.props import (BoolProperty, PointerProperty, StringProperty, EnumProperty)


                    # GLOBAL VARIABLES & DEFINES


isFalse = " is False: No changes made"

def clearTransforms(context):
    for ob in context.selected_objects:
            if ob.type == 'MESH':
                ob.rotation_euler, ob.location, ob.scale  = (0,0,0), (0,0,0), (1,1,1)
    return{'FINISHED'}

def deleteLooseGeometry(context):
    for ob in context.selected_objects:
        loose_mode_callback = context.object.mode
        if ob.type == 'MESH':
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.mesh.select_all(action = 'SELECT')
            bpy.ops.mesh.delete_loose()
        bpy.ops.object.mode_set(mode=loose_mode_callback)
    return{'FINISHED'}

def sharpsFromUVIslands(context):
    sharpsModeCallback = context.object.mode
    bpy.ops.object.mode_set(mode = 'OBJECT')
    for ob in context.selected_objects:
        if ob.type == 'MESH':
            bpy.ops.object.shade_smooth()
            ob.data.use_auto_smooth = True
            ob.data.auto_smooth_angle = 3.14159
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.uv.seams_from_islands(mark_seams=False, mark_sharp=True)
    bpy.ops.object.mode_set(mode = sharpsModeCallback)
    return {'FINISHED'}

def selectChildren(obj): 
  children = [] 
  for ob in bpy.data.objects: 
      if ob.parent == obj: 
          children.append(ob) 
  return children 


                    # OPERATIONS & BOOLS


class smartExportSettings(PropertyGroup):

    # Destructive

    deleteAnimData_D : BoolProperty(
        description = "Deletes all Animation Data")

    triangulateSelected_D : BoolProperty(
        description = "Adds a Triangulate Modifier")

    recalculateActivesNormals_D : BoolProperty(
        description = "Recalculates the direction of the normals")

    deleteLooseGeo_D : BoolProperty(
        description = "Deletes loose geometry")

    removeOverlappingVertices_D : BoolProperty(
        description = "Welds / removes overlapping vertices")

    sharpsfromUVIslands_D : BoolProperty(
        description = "Marks Sharps based on the UV Islands")

    clearTransforms_D : BoolProperty(
        description = "Sets all Transforms of the each object to their default values (Latest applied transform)")

    applyTransforms_D : BoolProperty(
        description = "Applies all Transforms of each object to their default values")

    # Non-destructive

    applyModifiers_NonD : BoolProperty(
        description="Applies Modifiers on export",
        default = True)
    
    filePerObject_NonD : BoolProperty(
        description = "Exports every object / collection to their own respective file")

    disableAllFunctions_NonD : BoolProperty(
        description = "If enabled, disables all functions below this option")

    triangulateSelected_NonD : BoolProperty(
        description = "Triangulates every mesh")

    deleteAnimData_NonD : BoolProperty(
        description = "Deletes all Animation Data")
    
    deleteLooseGeo_NonD : BoolProperty(
        description = "Deletes loose geometry")

    sharpsfromUVIslands_NonD : BoolProperty(
        description = "(NOTICE: This also enables Auto Smooth Normals) Marks Sharps based on the UV Islands")

    removeOverlappingVertices_NonD : BoolProperty(
        description = "Welds overlapping vertices")

    applyTransforms_NonD : BoolProperty(
        description = "Applies all Transforms of each object to their default values")

    changeTransforms_NonD : BoolProperty(
        description = "")

class openFolder(Operator):
    bl_idname = "op.openfolder"
    bl_label = ""
    bl_description = "Opens up the File Explorer with the designated folder location"
    bl_options = {'REGISTER'}

    def execute(self, context):
        if len(context.scene.confPath) <= 2:
            self.report({'ERROR'}, "There is no folder path is set")
        else:
            bpy.ops.wm.path_open(filepath = context.scene.confPath)
        return{'FINISHED'}

class removeTriangulate(Operator):
    bl_idname = "mesh.remove_tri"
    bl_label = ""
    bl_description = "Removes the Triangulate Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for ob in context.selected_objects:
            for mod in ob.modifiers:
                if(mod.type == "TRIANGULATE"):
                    ob.modifiers.remove(mod)
                    self.report({'INFO'}, "Triangulate Modifier removed")
        return{'FINISHED'}

class manualRefresher(Operator):
    bl_idname = "mesh.ref_manual"
    bl_label = ""
    bl_description = "Removes the Triangulate Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences

        context.scene.confPath = addon_prefs.filepath_Pref

        context.scene.exportType = addon_prefs.selection_Pref
        return{'FINISHED'}

class meshSetup(Operator):
    bl_idname = "op.mesh_setup"
    bl_label = "Smart Setup"
    bl_description = "This runs any of the corresponding functions that are enabled via checkbox below on your selected mesh(es)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):
        
        exportPrefs = context.scene.exportPrefs

        # Save Selection, Active & Context Mode

        setupSelectedCallback = context.view_layer.objects.selected.keys()
        setupActiveCallback = context.view_layer.objects.active.name
        setupModeCallback = context.object.mode

        # Check if all objects are meshes

        for ob in context.selected_objects:
            if ob.type != 'MESH' and ob.type != 'ARMATURE': # Requires Armature support pass
                self.report({'ERROR'}, "This operation can only be run on meshes & armatures containing meshes ")
                return{'FINISHED'}

        # Run operations

        print("\n  -- STARTING SMART MESH SETUP -- \n")

        if exportPrefs.sharpsfromUVIslands_D:
            print(" 'Setting UV Islands to Sharp' is True:")

            sharpsFromUVIslands(context)

        else:
            print(" 'Setting UV Islands to Sharp'" + isFalse)
            
        if exportPrefs.deleteAnimData_D:
            print("\n 'Delete Animation Data' is True:")

            bpy.ops.anim.keyframe_clear_v3d()

        else:
            print("\n 'Delete Animation Data'" + isFalse)
            
        if exportPrefs.triangulateSelected_D:
            print("\n 'Triangulate Selected w/ Modifier' is True:")

            for ob in context.selected_objects:
                if ob.type == 'MESH':
                    for mod in ob.modifiers:
                        if mod.type == "TRIANGULATE":
                            print("\n     " + ob.name + " already has a Triangulate Modifier; breaking")
                            break
                    else:
                        print("\n     " + ob.name + " has had a Triangulate Modifier added to it")
                        ob.modifiers.new('Triangulate', 'TRIANGULATE')

        else:
            print("\n 'Triangulate Selected with Modifier'" + isFalse) 
            
        if exportPrefs.recalculateActivesNormals_D:
            print("\n 'Recalculate Active(s) Normals' is True:")

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.normals_make_consistent(inside=False)

        else:
            print("\n 'Recalculate Active(s) Normals'" + isFalse)
            
        if exportPrefs.clearTransforms_D:
            print("\n 'Clear Transforms' is True:")

            clearTransforms(context)

        else:
            print("\n 'Clear Transforms'" + isFalse)
            
        if exportPrefs.deleteLooseGeo_D:
            print("\n 'Delete Loose Geometry' is True:")

            deleteLooseGeometry(context)

        else:
            print("\n 'Delete Loose Geometry'" + isFalse)  
            
        if exportPrefs.removeOverlappingVertices_D:
            print("\n 'Remove Overlapping Vertices' is True:")

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles()

        else:
            print("\n 'Remove Overlapping Vertices'" + isFalse)
        
        if exportPrefs.applyTransforms_D:
            print("\n 'Clear Transforms' is True:" + "\n")

            # Insert Code

        else:
            print("\n 'Clear Transforms'" + isFalse + "\n")

        # Set to Object Mode

        bpy.ops.object.mode_set(mode='OBJECT')

        # De-Select Everything

        bpy.ops.object.select_all(action='DESELECT')

        # Select original object(s)

        for o in setupSelectedCallback:
            ob = context.scene.objects.get(o)
            if ob:
                ob.select_set(True)
       
        # Select Active object

        context.view_layer.objects.active = bpy.data.objects[setupActiveCallback]

        # Set original Context Mode

        bpy.ops.object.mode_set(mode=setupModeCallback)
 
        self.report({'INFO'}, "Check System Console for changes made")
        return {'FINISHED'}

class smartExport(Operator):
    bl_idname = "op.smart_export"
    bl_label = "Smart Export"
    bl_description = "Quickly exports based on set options below. (NOTICE: If you export multiple objects designated to a single file, the file name will be based on the current Active Object)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        print("\n  -- STARTING SMART EXPORTER -- \n")


            # General Checks & Mesh Prep
         
        # Variables

        wasDuplicated = False
        exportPrefs = context.scene.exportPrefs
        checkIfOpsDisabled = exportPrefs.disableAllFunctions_NonD or not exportPrefs.applyTransforms_NonD and not exportPrefs.triangulateSelected_NonD and not exportPrefs.deleteAnimData_NonD and not exportPrefs.deleteLooseGeo_NonD and not exportPrefs.sharpsfromUVIslands_NonD and not exportPrefs.removeOverlappingVertices_NonD and not exportPrefs.changeTransforms_NonD

        # Check if the file path is set
        
        if os.path.exists(context.scene.confPath) == False:
            self.report({'ERROR'}, "There is no file path set")
            return{'FINISHED'}

        # Check if 'Export Selected' is True & if any objects are selected & if an active object is select

        if context.scene.exportType == "Selected":
            if not context.selected_objects:
                self.report({'ERROR'}, "There is no Object(s) selected")
                return{'FINISHED'}

        if context.view_layer.objects.active == None:
            self.report({'ERROR'}, "There is no Active Object Selected")
            return{'FINISHED'}

#        # Check if any Armatures are named "armature" (and proptly rename it if they are)
#
#        for ob in context.selected_objects:
#            if ob.name == "Armature" and ob.type == 'ARMATURE':
#                ob.name = ob.name + "_Rig"
#                self.report({'ERROR'}, "Your Armature(s) named 'Armature' have been automatically renamed since some engines don't accept that naming convention")
#                return{'FINISHED'}
 
        # Save Context Mode

        exportModeCallback = context.object.mode
        
        # Visible Selected

        visibleSelected = context.view_layer.objects.selected.keys()
        visibleSelectedActive = context.view_layer.objects.active.name

        # Check if Export Collections is enabled

        if context.scene.exportType == "Collections":

            # Check if there are any collections in the scene

            if not bpy.data.collections:
                self.report({'ERROR'}, "There are no collections in the scene to export (Smart Export does not work with the Master Collection)")
                return{'FINISHED'}

            currentvLayer = bpy.context.view_layer.name
            vLayer = bpy.context.scene.view_layers[currentvLayer]

            for coll in bpy.data.collections:
                if vLayer.layer_collection.children[coll.name].is_visible:
                    savedcollection = coll.name
                    for ob in coll.objects:
                        if savedcollection == coll.name:
                            ob.select_set(True)

        if context.scene.exportType == "Visible":
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='SELECT')

        # Give original object(s) a temporary suffix
        
        if checkIfOpsDisabled == False:
            wasDuplicated = True
            for ob in context.selected_objects:
                ob.name = ob.name + "_TEMP"

            visibleSelected = context.view_layer.objects.selected.keys()
            visibleSelectedActive = context.view_layer.objects.active.name

        # Save the Selection + the Active

        selected = context.view_layer.objects.selected.keys()
        selectedActive = context.view_layer.objects.active.name

        # Set if Modifiers will be Applied on export

        if exportPrefs.applyModifiers_NonD:
            modapplychoice = True
        else:
            modapplychoice = False


            # Operations & Operation Checks


        # Check if all operations are disabled

        if wasDuplicated:

            bpy.ops.object.mode_set(mode='OBJECT')

#            # Check if the Active Object is an Armature
#
#            if context.view_layer.objects.active.type == 'ARMATURE':
#                self.report({'ERROR'}, "The Active object cannot be an Armature when you have operations running")
#                for ob in context.selected_objects:
#                    ob.name = ob.name[:-5]
#                return{'FINISHED'}

            # De-select everything but the Armatures

            for ob in context.selected_objects:
                if ob.type != 'ARMATURE':
                    ob.select_set(False)

            # Save Armature selection

            armatureselection = context.view_layer.objects.selected.keys()

            # Select all objects except for the Armatures but grab the armatures children

            bpy.ops.object.select_all(action='DESELECT')

            for o in selected:
                ob = context.scene.objects.get(o)
                if ob:
                    ob.select_set(True)
                    for child in selectChildren(ob):
                        child.select_set(state=True)
                        if ob.type == 'ARMATURE':
                            ob.select_set(False)

            # Duplicate the object(s)

            bpy.ops.object.duplicate()

            # Remove .001 & temporary suffix from duplicated meshes

            for ob in context.selected_objects:
                ob.name = ob.name[:-9]
                ob.name = ob.name + "_DUP"

            # Save Duplicated object(s) selection

            duplicatedSelected = context.view_layer.objects.selected.keys()
            duplicatedSelectedActive = context.view_layer.objects.active.name

            # Begin operations on the object(s)

            if exportPrefs.triangulateSelected_NonD:
                print("\n'Triangulate Selected' is True:")
                for ob in context.selected_objects:
                    if ob.type == 'MESH':
                        for mod in ob.modifiers:
                            if mod.type == 'TRIANGULATE':
                                bpy.ops.object.modifier_apply(modifier="Triangulate")
                        else:
                            ob.modifiers.new('Triangulate', 'TRIANGULATE')
                            bpy.ops.object.modifier_apply(modifier="Triangulate")
            else:
                print("\n'Triangulate Selected'" + isFalse)

            if exportPrefs.removeOverlappingVertices_NonD: # Make sure this actually works
                print("\n'Remove / Weld Overlapping Vertices' is True:")
                for ob in context.selected_objects:
                    if ob.type == 'MESH':
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='SELECT')
                        bpy.ops.mesh.remove_doubles()
            else:
                print("\n'Remove Overlapping Vertices'" + isFalse)

            if exportPrefs.deleteAnimData_NonD:
                print("\n'Delete Animation Data' is True:")
                bpy.ops.anim.keyframe_clear_v3d()
            else:
                print("\n'Delete Animation Data'" + isFalse)

            if exportPrefs.deleteLooseGeo_NonD:
                print("\n'Delete Loose Geometry' is True:")
                deleteLooseGeometry(context)
            else:
                print("\n'Delete Loose Geometry'" + isFalse)

            if exportPrefs.sharpsfromUVIslands_NonD:
                print("\n'Mark Sharps from UV Islands' is True:")
                sharpsFromUVIslands(context)
            else:
                print("\n'Mark Sharps from UV Islands'" + isFalse)

            if exportPrefs.changeTransforms_NonD:
                if context.scene.transformType == "Center Transforms":
                    print("\n'Center Transforms' is True:")

                    bpy.ops.object.mode_set(mode='OBJECT')
                    for ob in context.selected_objects:
                        if ob.type == 'MESH':
                            bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')
                            ob.rotation_euler, ob.location, ob.scale  = (0,0,0), (0,0,0), (1,1,1)

                    print("\n'Clear Transforms'" + isFalse) 
                else:
                    print("\n'Clear Transforms' is True:")
                    clearTransforms(context)
                    print("\n'Center Transforms'" + isFalse)
            else:
                print("\n'Clear Transforms'" + isFalse + "\n\n'Center Transforms'" + isFalse)

            if exportPrefs.applyTransforms_NonD:
                print("\n'Apply Transforms' is True:")

                bpy.ops.object.mode_set(mode='OBJECT')

                for ob in context.selected_objects:
                    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

            else:
                print("\n'Apply Transforms'" + isFalse) 

            # Go to to object mode and re-select all original duplicated objects

            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.ops.object.select_all(action='DESELECT')

            for o in duplicatedSelected:
                ob = context.scene.objects.get(o)
                if ob:
                    ob.select_set(True)

            context.view_layer.objects.active = bpy.data.objects[duplicatedSelectedActive]


            # Export Prep & Export


        bpy.ops.object.mode_set(mode='OBJECT')

        if context.scene.exportType == "Collections":

            currentvLayer = bpy.context.view_layer.name
            vLayer = bpy.context.scene.view_layers[currentvLayer]

            if wasDuplicated:
                for coll in bpy.data.collections:
                    bpy.ops.object.select_all(action='DESELECT') 
                    if vLayer.layer_collection.children[coll.name].is_visible:
                        savedcollection = coll.name
                        for ob in coll.objects:
                            if savedcollection == coll.name:
                                if ob.name.endswith('_DUP'):
                                    ob.select_set(True)
                                    ob.name = ob.name[:-4]

                        # Export

                        if coll.objects:

                            bpy.ops.export_scene.fbx(filepath=context.scene.confPath + coll.name + ".fbx",
                                                     filter_glob="*.fbx",
                                                     use_mesh_modifiers=modapplychoice,
                                                     use_selection=True,
                                                     use_armature_deform_only=True,
                                                     add_leaf_bones=False,
                                                     path_mode='ABSOLUTE')

                            for ob in context.selected_objects:
                                ob.name = ob.name + '_DUP'

            else:

                for coll in bpy.data.collections:
                    bpy.ops.object.select_all(action='DESELECT') 
                    if vLayer.layer_collection.children[coll.name].is_visible:
                        savedcollection = coll.name
                        for ob in coll.objects:
                            if savedcollection == coll.name:
                                    ob.select_set(True)

                    # Export

                        if coll.objects:

                            bpy.ops.export_scene.fbx(filepath=context.scene.confPath + coll.name + ".fbx",
                                                     filter_glob="*.fbx",
                                                     use_mesh_modifiers=modapplychoice,
                                                     use_selection=True,
                                                     use_armature_deform_only=True,
                                                     add_leaf_bones=False,
                                                     path_mode='ABSOLUTE')
        
        else:

            if exportPrefs.filePerObject_NonD:
                for ob in context.selected_objects:
                    bpy.ops.object.select_all(action='DESELECT')
                    ob.select_set(True)
                    if wasDuplicated:
                        ob.name = ob.name[:-4]

                    # Export

                    bpy.ops.export_scene.fbx(filepath=context.scene.confPath + ob.name + ".fbx",
                                                filter_glob="*.fbx",
                                                use_mesh_modifiers=modapplychoice,
                                                use_selection=True,
                                                use_armature_deform_only=True,
                                                add_leaf_bones=False,
                                                path_mode='ABSOLUTE')

                    if wasDuplicated:
                        for ob in context.selected_objects:
                            ob.name = ob.name + "_DUP"

            else:
                if wasDuplicated:
                    for ob in context.selected_objects:
                        ob.name = ob.name[:-4]

                # Export
            
                bpy.ops.export_scene.fbx(filepath=context.scene.confPath + context.view_layer.objects.active.name + ".fbx",
                                         filter_glob="*.fbx",
                                         use_mesh_modifiers=modapplychoice,
                                         use_selection=True,
                                         use_armature_deform_only=True,
                                         add_leaf_bones=False,
                                         path_mode='ABSOLUTE')
                
                if wasDuplicated:
                    for ob in context.selected_objects:
                            ob.name = ob.name + "_DUP"

#for o in selected:
#    ob = context.scene.objects.get(o)
#    if ob.type == 'ARMATURE':
#        ob.select_set(True)
#
# Select children if they exist
#
#for ob in context.selected_objects:
#    for child in selectChildren(ob):
#        child.select_set(state=True)


            # Final Clean Up


        bpy.ops.object.select_all(action='DESELECT')

        if wasDuplicated:

            # Select only duplicated object(s)

            for o in duplicatedSelected:
                ob = context.scene.objects.get(o)
                if ob:
                    ob.select_set(True)

            context.view_layer.objects.active = bpy.data.objects[duplicatedSelectedActive]

            # Delete the duplicated object(s)

            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.delete(use_global=False)
        
        # Re-Select original object(s) & Call for original Context Mode
        if context.scene.exportType == "Collections" or context.scene.exportType == "Visible":

            for o in visibleSelected:
                ob = context.scene.objects.get(o)
                if ob:
                    ob.select_set(True)

            context.view_layer.objects.active = bpy.data.objects[visibleSelectedActive]

        else:

            for o in selected:
                ob = context.scene.objects.get(o)
                if ob:
                    ob.select_set(True)

            context.view_layer.objects.active = bpy.data.objects[selectedActive]
        
        if wasDuplicated:
            for ob in context.selected_objects:
                if ob.type == 'MESH':
                    ob.name = ob.name[:-5]

        bpy.ops.object.mode_set(mode=exportModeCallback)

        # Finishing confirmation message

        print("")
        self.report({'INFO'}, "Smart Export operation successful! Check Console for changes made.")
        return{'FINISHED'}

    # Refresh viewport thing

#view3d = []
#
#for win in bpy.context.window_manager.windows:
#    for area in win.screen.areas:
#        if area.type == 'VIEW_3D':
#            view3d.append({'window' : win, 'area': area})
#
#for ob in bpy.context.selected_objects:
#    bpy.context.view_layer.objects.active = ob
#    for viewport in view3d:
#        viewport['area'].tag_redraw()


    # Confirm save thingy

#class SimpleConfirmOperator(bpy.types.Operator):
#    """Save Preset? (This Operation Saves User Preferences)"""
#    bl_idname = "my_category.custom_confirm_dialog"
#    bl_label = "Save Preset? (This Operation Saves User Preferences)"
#    bl_options = {'REGISTER', 'INTERNAL'}
#
#    @classmethod
#    def poll(cls, context):
#        return True
#
#    def execute(self, context):
#        self.report({'INFO'}, "YES!")
#        return {'FINISHED'}
#
#    def invoke(self, context, event):
#        if context.preferences.use_preferences_save == False:
#            return context.window_manager.invoke_confirm(self, event)
#        else:
#            print("nothing to see here")
#        return{'FINISHED'}

#class OBJECT_PT_CustomPanel(bpy.types.Panel):
#    bl_label = "My Panel"
#    bl_idname = "OBJECT_PT_custom_panel"
#    bl_space_type = "VIEW_3D"   
#    bl_region_type = "UI"
#    bl_category = "Tools"
#    bl_context = "objectmode"
#
#    def draw(self, context):
#        layout = self.layout
#        layout.operator(SimpleConfirmOperator.bl_idname, text="Save Preset")


                    # KEYMAPPING


def get_hotkey_entry_item(km, kmi_name):
    for i, km_item in enumerate(km.keymap_items):
        if km.keymap_items.keys()[i] == kmi_name:
            return km_item
    return None

class keymappingPrefs(AddonPreferences):
    bl_idname = __name__

#    - Template for auto updates -
#
#    def update_removeOverlappingPref (self, context):
#        if self.removeOverlapping == True:
#            context.scene.exportPrefs.removeOverlappingVertices_NonD = True
#        else:
#            context.scene.exportPrefs.removeOverlappingVertices_NonD = False
#
#    update=update_removeOverlappingPref

        # DESTRUCTIVE OPERATIONS

    deleteAnimData_D_Pref : BoolProperty(
        description = "Deletes all Animation Data")

    triangulateSelected_D_Pref : BoolProperty(
        description = "Adds a Triangulate Modifier")

    recalculateActivesNormals_D_Pref : BoolProperty(
        description = "Recalculates the direction of the normals")

    deleteLooseGeo_D_Pref : BoolProperty(
        description = "Deletes loose geometry")

    removeOverlappingVertices_D_Pref : BoolProperty(
        description = "Welds / removes overlapping vertices")

    sharpsfromUVIslands_D_Pref : BoolProperty(
        description = "Marks Sharps based on the UV Islands")

    clearTransforms_D_Pref : BoolProperty(
        description = "Sets all Transforms of the each object to their default values (Latest applied transform)")

    applyTransforms_D_Pref : BoolProperty(
        description = "Applies all Transforms of each object to their default values")

    filepath_Pref : StringProperty(
        name="Path Preset",
        subtype='DIR_PATH')

    selection_Pref : EnumProperty(
        name = " ",
        items = [
            ("Visible", "Visible", "Exports all visible objects in the scene"),
            ("Selected", "Selected", "Exports only selected objects in the scene"),
            ("Collections", "Collections", "Exports all visible objects in visible collections in the scene to their own files per collection (NOTICE: This function entirely disregards 'File Per Object')")
            ],
        )

    def draw(self, context):
        layout = self.layout
        exportprefs = context.scene.exportPrefs
        box = layout.box()
        row = box.row()
        row.prop(self, 'filepath_Pref')
        row = box.row()
        row = box.row()
        row.label(text="Selection Preset:")
        row.prop(self, 'selection_Pref', expand=True)
        row = layout.row()
        row.label(text='Mesh Setup Preferences:')
        box = layout.box()
        row = box.row()
        row.prop(self, 'deleteAnimData_D_Pref', text = "Delete Animation Data")
        row.prop(self, 'triangulateSelected_D_Pref', text = "Triangulate (w/ Modifier)")
        row.prop(self, 'recalculateActivesNormals_D_Pref', text = "Recalculate Normals")
        row = box.row()
        row.prop(self, 'deleteLooseGeo_D_Pref', text = "Delete Loose Geometry")
        row.prop(self, 'removeOverlappingVertices_D_Pref', text = "Weld Overlapping Verices")
        row.prop(self, 'sharpsfromUVIslands_D_Pref', text = "Mark Sharps from UV Islands")
        row = box.row()
        row.prop(self, 'clearTransforms_D_Pref', text = "Clear Transforms")
        row.prop(self, 'applyTransforms_D_Pref', text = "Apply Transforms")

        wm = bpy.context.window_manager
        row = layout.row()
        row.label(text='Hotkeys:')
        box = layout.box()
        split = box.split()
        col = split.column()
        kc = wm.keyconfigs.user
        km = kc.keymaps['3D View']
        kmi = get_hotkey_entry_item(km, 'op.mesh_setup')
        col.context_pointer_set("keymap", km)
        rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        kmi = get_hotkey_entry_item(km, 'op.smart_export')
        col.context_pointer_set("keymap", km)
        rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)

addon_keymaps = []


                    # UI


class meshSetupUI(Panel):
    bl_idname = "MESHSETUP_PT_UI"
    bl_label = 'Smart Mesh Setup (Destructive)'
    bl_category = 'Mesh Setup / Exporter'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    def draw(self, context):
        layout = self.layout
        exportprefs = context.scene.exportPrefs

        box = layout.box()
        row = box.row()
        row.scale_y = 1.5
        row.operator("op.mesh_setup", text = "Run on Selected Object(s)")
        row = box.row()
        row.prop(exportprefs, 'deleteAnimData_D', text = "Delete Animation Data")
        row = box.row()
        row.prop(exportprefs, 'triangulateSelected_D', text = "Triangulate (w/ Modifier)")
        row.operator("mesh.remove_tri", icon = "CANCEL")
        row = box.row()
        row.prop(exportprefs, 'recalculateActivesNormals_D', text = "Recalculate Normals")
        row = box.row()
        row.prop(exportprefs, 'deleteLooseGeo_D', text = "Delete Loose Geometry")
        row = box.row()
        row.prop(exportprefs, 'removeOverlappingVertices_D', text = "Weld Overlapping Vertices")
        row = box.row()
        row.prop(exportprefs, 'sharpsfromUVIslands_D', text = "Mark Sharps from UV Islands")
        row = box.row()
        row.prop(exportprefs, 'clearTransforms_D', text = "Clear Transforms")
        row = box.row()
        row.prop(exportprefs, 'applyTransforms_D', text = "_Apply Transforms")

class exporterUI(Panel):
    bl_idname = "EXPORTER_PT_UI"
    bl_label = 'Smart Mesh Exporter (Non-Destructive)'
    bl_category = 'Mesh Setup / Exporter'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        exportprefs = context.scene.exportPrefs
        scene = context.scene

        box = layout.box()
        row = box.row(align=True)
        row.scale_y = 1.5
        row.operator("op.smart_export", text = "Quick Export")
        row = box.row()
        row = box.row(align=True)
        row.prop(scene, 'confPath')
        row.operator("op.openfolder", text = "", icon = "FILE_PARENT")
        row = box.row()
        row = box.row()
        row.label(text="Selection:")
        row.prop(scene, "exportType", expand=True)
        row = box.row()
        row = box.row()
        row.alignment = 'CENTER'
        row.prop(exportprefs, 'applyModifiers_NonD' ,text = "Apply Modifiers")
        split = row.split()
        if context.scene.exportType == "Collections":
            split.active = False
        else:
            split.active = True
        split.alignment = 'CENTER'
        split.prop(exportprefs, 'filePerObject_NonD' ,text = "File Per Object")
        box = layout.box()
        row = box.row()
        row = box.row()
        row.alignment = 'CENTER'
        row.prop(exportprefs, 'disableAllFunctions_NonD',text = "Disable All Operators")
        row = box.row()
        row.prop(exportprefs, 'deleteAnimData_NonD', text = "Delete Anim Data")
        row.prop(exportprefs, 'triangulateSelected_NonD', text = "Triangulate")
        row = box.row()
        row.prop(exportprefs, 'deleteLooseGeo_NonD', text = "Delete Loose")
        row.prop(exportprefs, 'removeOverlappingVertices_NonD', text = "Weld Overlapping")
        row = box.row()
        row.prop(exportprefs, 'sharpsfromUVIslands_NonD', text = "Mark Sharps from UV Islands")
        row = box.row()
        row.scale_x = 1.5
        row.prop(exportprefs, 'changeTransforms_NonD', text = "Transforms:")
        row.prop(scene, "transformType", expand=True)
        row = box.row()
        row.prop(exportprefs, 'applyTransforms_NonD', text = "Apply Transforms")

class otherUI(Panel):
    bl_idname = "OTHER_PT_UI"
    bl_label = 'Other Stuff'
    bl_category = 'Mesh Setup / Exporter'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        exportprefs = context.scene.exportPrefs
        scene = context.scene

        row = layout.row()
        row.operator("mesh.ref_manual", text = "Save Preset", icon = "EXPORT")
        row.operator("mesh.ref_manual", text = "Load Preset", icon = "IMPORT")
        row = layout.row()
        row.operator('wm.url_open', text = "Documentation", icon = "QUESTION").url = "https://gdoc.pub/doc/e/2PACX-1vSIqOGhZuRAH_DQdCsRli4KoZGF-ngviGYuSTO0U_twBs6mg6D2DpXuiGIy9k1IMIDp4KQDxQ_MWI5x"


                    # REGISTRATION


classes = (
smartExportSettings,
openFolder,
removeTriangulate,
manualRefresher,
meshSetup,
smartExport,
keymappingPrefs,
meshSetupUI,
exporterUI,
otherUI)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.exportPrefs = PointerProperty(type=smartExportSettings)
    bpy.types.Scene.directory = StringProperty(subtype='DIR_PATH')
    bpy.types.Scene.confPath = bpy.props.StringProperty \
        (
            name = "Path",
            default = "",
            description = "Define the root path of the project",
            subtype = 'DIR_PATH')

    bpy.types.Scene.transformType = bpy.props.EnumProperty(
        name = " ",
        items = [
            ("Clear Transforms", "Clear", "Clears transforms to their default values"),
            ("Center Transforms", "Center", "Centers the origins on every exported object and sets them to their default values")],)

    bpy.types.Scene.exportType = bpy.props.EnumProperty(
        name = " ",
        items = [
            ("Visible", "Visible", "Exports all visible objects in the scene"),
            ("Selected", "Selected", "Exports only selected objects in the scene"),
            ("Collections", "Collections", "Exports all visible objects in visible collections in the scene to their own files per collection (NOTICE: This function entirely disregards 'File Per Object')")],)
    
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new('op.smart_export', 'E', 'PRESS', ctrl=True, alt=True)
        kmi = km.keymap_items.new('op.mesh_setup', 'R', 'PRESS', ctrl=True, alt=True)
        addon_keymaps.append((km, kmi))

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.exportPrefs
    del bpy.types.Scene.confPath

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()