# Copyright (C) 2019 h0bB1T
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
#
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

import bpy, os

from bpy.types              import Panel, WindowManager
from bpy.props              import EnumProperty, StringProperty

from . utils                import textures_of_objects, categories, categories_enum, export_file, export_file_exists, ASSET_TYPE_OBJECT, ASSET_TYPE_MATERIAL
from . preferences          import PreferencesPanel
from . preview_helper       import PreviewHelper
from . properties           import Properties
from . create_category_ops  import CreateCategoryOperator
from . exporter_ops         import UseObjectNameOperator, OverwriteObjectExporterOperator, TexturePackSelectionOperator, ObjectExporterOperator
from . importer_ops         import (AppendObjectOperator, LinkObjectOperator, 
                                    SetMaterialOperator, AppendMaterialOperator, OpenObjectOperator, OpenMaterialOperator)
from . render_previews_ops  import RenderPreviewsOperator,RenderAllPreviewsOperator        
from . generate_ops         import GeneratePBROperator, GenerateImageOperator, ExportPBROperator, ExportMaterialOperator             
from . node_importer_ops    import NodeImporter  
from . ao_curv_calc_ops     import BakeAoMapOperator, CurvatureMapOperator, AoNodeOperator, CurvatureNodeOperator, MapGenerateUV, UseObjectNameForMap
from . tools_ops            import (DX2OGLConverterOperator, GenerateTwoLayerTextureBasedSetupOperator,
                                        GenerateTwoLayerShaderBasedSetupOperator, ImportDistortionOperator,
                                        ImportBlurOperator, ImportTextureBoxMapUVW, ImportExtNoise,
                                        ImportExtMusgrave, ImportExtVoronoi, ImportMixNoise,
                                        ImportScalarMix, ImportIntensityVisualizer, ImportScalarMapper,
                                        ImportNormalDirection, ImportSlice)      
from . support_ops          import RefreshObjectPreviews, ReRenderObjectPreview, RefreshMaterialPreviews, ReRenderMaterialPreview, RemoveAsset

class ImportPanel(Panel):
    """
    The panel for object and material import.
    """
    bl_idname = "OBJECT_PT_assetwizard_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Asset Wizard Manager"
    bl_category = "Asset Wizard"

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'


    # Draw
    def draw(self, context):
        prefs = PreferencesPanel.get()
        compact = prefs.compact_panels
        preview_scale = 5.0 * prefs.preview_scale
        properties = Properties.get()

        box = self.layout.box()

        objcats = categories_enum(ASSET_TYPE_OBJECT)
        matcats = categories_enum(ASSET_TYPE_MATERIAL)

        if objcats or matcats:
            # In case of empty asset-object-lib:
            if objcats:
                if not compact:
                    box.row().label(text="Objects")

                col = box.column(align=True)
                col.prop(properties, "iobj_categories")
                col.template_icon_view(
                    properties, 
                    "iobj_previews", 
                    show_labels=True,
                    scale=preview_scale
                )
                split = col.row(align=True).split(factor=0.5, align=True)
                split.operator(RefreshObjectPreviews.bl_idname, icon="FILE_REFRESH")
                split.operator(ReRenderObjectPreview.bl_idname, icon="RENDER_STILL")

                split_outer = col.row(align=True).split(factor=0.9, align=True)
                is_fbx = properties.iobj_previews.lower().endswith(".fbx")
                if is_fbx:
                    split_outer.operator(AppendObjectOperator.bl_idname, icon="ADD")
                else:
                    split = split_outer.split(factor=0.333, align=True)
                    split.operator(AppendObjectOperator.bl_idname, icon="ADD")
                    split.operator(LinkObjectOperator.bl_idname, icon="LINK_BLEND")
                    split.operator(OpenObjectOperator.bl_idname, icon="FILE")
                op = split_outer.operator(RemoveAsset.bl_idname, icon="PANEL_CLOSE", text="")
                op.asset_type = ASSET_TYPE_OBJECT
                op.asset = properties.iobj_previews

                split = col.row(align=True).split(factor=0.5, align=True)
                split.prop(properties, "iobj_at_cursor", toggle=True, icon="PIVOT_CURSOR")
                split.prop(properties, "iobj_lock_xy", toggle=True, icon="VIEW_PERSPECTIVE")

            else:
                box.label(text="No object categories yet")
                box.label(text="(Create in Asset Wizard Export)")

            # In case of empty asset-material-lib:
            if matcats:
                if not compact:
                    box = self.layout.box()
                    box.row().label(text="Materials")

                col = box.column(align=True)
                col.prop(properties, "imat_categories") 
                col.template_icon_view(
                    properties, 
                    "imat_previews", 
                    show_labels=True,
                    scale=preview_scale
                    )
                split = col.row(align=True).split(factor=0.5, align=True)
                split.operator(RefreshMaterialPreviews.bl_idname, icon="FILE_REFRESH")
                split.operator(ReRenderMaterialPreview.bl_idname, icon="RENDER_STILL")
                split = col.row(align=True).split(factor=0.333, align=True)
                split.operator(SetMaterialOperator.bl_idname, icon="LINK_BLEND")
                split.operator(AppendMaterialOperator.bl_idname, icon="ADD")
                split.operator(OpenMaterialOperator.bl_idname, icon="FILE")
                #op = split.operator(RemoveAsset.bl_idname, icon="REMOVE")
                #op.asset_type = ASSET_TYPE_MATERIAL
                #op.asset = properties.imat_previews

            else:
                box.label(text="No material categories yet")
                box.label(text="(Create in Node Wizard Export)")
        else:
            # Neighter obj nor mat categories.
            col = box.column(align=True)
            col.row(align=True).label(text="No object or material categories yet")
            col.row(align=True).label(text="(Create in Asset Wizard Export")
            col.row(align=True).label(text="or Node Wizard Export)")

        if not compact:
            box = self.layout.box()

            box.row().label(text="Render Previews")
        split = box.row(align=True).split(factor=0.5, align=True)
        split.operator(RenderPreviewsOperator.bl_idname, icon="RENDER_STILL")
        split.operator(RenderAllPreviewsOperator.bl_idname, icon="RENDER_STILL")    

        # Current background render status.
        status = Properties.get_render_previews().status()
        if status:
            col = box.column(align=True)
            for line in status.split("::"):
                col.row(align=True).label(text=line)


class ExportPanel(Panel):
    """
    The panel for object export.
    """
    bl_idname = "OBJECT_PT_assetwizard_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Asset Wizard Exporter"
    bl_category = "Asset Wizard"

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and len(context.selected_objects) > 0


    def draw(self, context):
        prefs = PreferencesPanel.get()
        properties = Properties.get()

        compact = prefs.compact_panels
        if properties.eobj_pack_textures == None:
            properties.eobj_pack_textures = prefs.pack_textures_by_default

        box = self.layout.box()

        # In case of empty asset-object-lib:
        if categories(ASSET_TYPE_OBJECT):
            if not compact:
                box.row().label(text="Target Rotation & Location:")
                box.row().prop(properties, "eobj_rotation", expand=True, toggle=True)
                box.row().prop(properties, "eobj_location", expand=True)
                box.row().label(text="Rename Objects:")
                box.row().prop(properties, "eobj_rename", expand=True)
                box.row().label(text="Rename Materials:")
                box.row().prop(properties, "eobj_rename_material", expand=True)      
            else:
                col = box.column(align=True)
                col.row(align=True).prop(properties, "eobj_rotation", expand=True, toggle=True)
                col.row(align=True).prop(properties, "eobj_location", expand=True)
                col.row(align=True).prop(properties, "eobj_rename", expand=True)
                col.row(align=True).prop(properties, "eobj_rename_material", expand=True)      

                
            if not compact:
                box = self.layout.box()
                box.row().label(text="Output Category:")

            col = box.column(align=True)
            col.row(align=True).prop(properties, "eobj_new_categories")
            split = col.row(align=True).split(factor=0.9, align=True)
            split.prop(properties, "eobj_new_category")
            op = split.operator(CreateCategoryOperator.bl_idname, text="", icon='ADD')
            op.asset_type = ASSET_TYPE_OBJECT
            op.category = properties.eobj_new_category
            op.top_category = properties.eobj_new_categories

            if not compact:
                box.row().label(text="Export Settings:")

            col = box.column(align=True)
            col.row(align=True).prop(properties, "eobj_export_type", expand=True)
            if properties.eobj_export_type == '0':
                col.row(align=True).prop(properties, "eobj_pack_textures", expand=True, toggle=True, icon='PACKAGE')
            col.row(align=True).prop(properties, "eobj_categories")
            split = col.row(align=True).split(factor=0.9, align=True)
            split.prop(properties, "eobj_asset_name", expand=True)
            split.operator(UseObjectNameOperator.bl_idname, icon="URL", text="")

            # Select operator depending if output file already exists.
            if export_file_exists(
                ASSET_TYPE_OBJECT, 
                properties.eobj_categories, 
                properties.eobj_asset_name, 
                Properties.export_type_ext(properties.eobj_export_type)):
                op = col.row(align=True).operator(OverwriteObjectExporterOperator.bl_idname, icon="EXPORT")
            else:
                # Only if export to blend and pack textures is enabled .. and if at least one texture can be packed.
                if properties.eobj_export_type == '0' and properties.eobj_pack_textures and len(textures_of_objects(context.selected_objects)) > 0:
                    op = col.row(align=True).operator(TexturePackSelectionOperator.bl_idname, icon="EXPORT")
                else:
                    op = col.row(align=True).operator(ObjectExporterOperator.bl_idname, icon="EXPORT")

            op.category = properties.eobj_categories
            op.asset_name = properties.eobj_asset_name
            op.pack_textures = properties.eobj_pack_textures
            op.location = properties.eobj_location
            op.rotation = properties.eobj_rotation
            op.rename = properties.eobj_rename
            op.rename_material = properties.eobj_rename_material
            op.export_type = properties.eobj_export_type
        else:
            box.label(text="No object categories yet, create one")
            col = box.column(align=True)
            col.row(align=True).prop(properties, "eobj_new_categories")
            split = col.row(align=True).split(factor=0.9, align=True)
            split.prop(properties, "eobj_new_category")
            op = split.operator(CreateCategoryOperator.bl_idname, text="", icon='ADD')
            op.asset_type = ASSET_TYPE_OBJECT
            op.category = properties.eobj_new_category
            op.top_category = properties.eobj_new_categories


class NodeWizardPanel(Panel):
    """
    The panel for node wizard (nodes space).
    """
    bl_idname = "MATERIAL_PT_assetwizard_nodewizard"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_label = "Node Wizard"
    bl_category = "Asset Wizard"

    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'NODE_EDITOR' and \
            context.space_data.node_tree is not None and \
            context.space_data.tree_type == 'ShaderNodeTree'


    def draw(self, context):
        prefs = PreferencesPanel.get()
        compact = prefs.compact_panels
        preview_scale = 5.0 * prefs.preview_scale
        properties = Properties.get()
        layout = self.layout

        box = layout.box()
        if not compact:
            box.label(text="Material from Textures")

        col = box.column(align=True)
        split = col.row(align=True).split(factor=0.5, align=True)
        op = split.operator(GeneratePBROperator.bl_idname, icon="UV")
        op.add_hslbc = properties.nw_add_hslbc
        op.add_uv = properties.nw_add_uv
        op.decal = properties.nw_decal
        op = split.operator(GenerateImageOperator.bl_idname, icon="UV")
        op.add_hslbc = properties.nw_add_hslbc
        op.add_uv = properties.nw_add_uv
        op.decal = properties.nw_decal
        row = col.row(align=True)
        split = row.split(factor=0.5, align=True)
        split.prop(properties, "nw_add_hslbc")
        split.prop(properties, "nw_add_uv")
        col.row().prop(properties, "nw_decal")

        #########################################

        if not compact:
            box = layout.box()
            box.label(text="Material Layers")

        row = box.row(align=True)
        split = row.split(factor=0.5, align=True)
        split.operator(GenerateTwoLayerShaderBasedSetupOperator.bl_idname, icon="RENDERLAYERS")
        split.operator(GenerateTwoLayerTextureBasedSetupOperator.bl_idname, icon="RENDERLAYERS")

        #########################################

        if not compact:
            box = layout.box()
            box.label(text="Vector Manipulation Nodes")

        col = box.column(align=True)
        row = col.row(align=True)
        split = row.split(align=True, factor=0.333)
        split.operator(ImportDistortionOperator.bl_idname)
        split.operator(ImportBlurOperator.bl_idname)
        split.operator(ImportTextureBoxMapUVW.bl_idname)

        if not compact:
            box = layout.box()
            box.label(text="Extended Procedural Nodes")
            col = box.column(align=True)

        row = col.row(align=True)
        split = row.split(align=True, factor=0.333)
        split.operator(ImportExtNoise.bl_idname)
        split.operator(ImportExtMusgrave.bl_idname)
        split.operator(ImportExtVoronoi.bl_idname)
        split = col.row(align=True).split(align=True, factor=0.333)
        split.operator(ImportMixNoise.bl_idname)        

        if not compact:
            box = layout.box()
            box.label(text="Utility Nodes")
            col = box.column(align=True)

        row = col.row(align=True)
        split = row.split(align=True, factor=0.333)
        split.operator(ImportIntensityVisualizer.bl_idname)        
        split.operator(DX2OGLConverterOperator.bl_idname)       
        split.operator(ImportScalarMix.bl_idname)      
        row = col.row(align=True)
        split = row.split(align=True, factor=0.333)
        split.operator(ImportScalarMapper.bl_idname)                  
        split.operator(ImportNormalDirection.bl_idname)                  
        split.operator(ImportSlice.bl_idname)                  

        #########################################

        if not compact:
            box = layout.box()
            box.label(text="Masks")

        col = box.column(align=True)
        col.row().template_icon_view(
            properties, 
            "nw_nodes_previews", 
            show_labels=True,
            scale=preview_scale
        )
        col.row().operator(NodeImporter.bl_idname, text="Add Mask", icon="ADD").group = properties.nw_nodes_previews

        if not compact:
            box.label(text="Materials")

        col = box.column(align=True)
        col.row().template_icon_view(
            properties, 
            "nw_materials_previews", 
            show_labels=True,
            scale=preview_scale
        )
        col.row().operator(NodeImporter.bl_idname, text="Add Material", icon="ADD").group = properties.nw_materials_previews


class NodeWizardMapPanel(Panel):
    """
    The panel for node wizard map generator (nodes space).
    """
    bl_idname = "MATERIAL_PT_assetwizard_nodewizard_map"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_label = "Node Wizard Map Generator"
    bl_category = "Asset Wizard"  

    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'NODE_EDITOR' and \
            context.space_data.node_tree is not None and \
            context.space_data.tree_type == 'ShaderNodeTree'


    def get_blend_path(self):
        """
        Return path to blend, None if not known (unsaved).
        """
        if len(bpy.data.filepath) == 0:
            return None

        return os.path.split(bpy.data.filepath)[0]

    
    def get_export_file(self, postfix):
        """
        Create export file name.
        """
        properties = Properties.get()
        filename = bpy.path.clean_name(properties.cao_export_map_basename) + \
            "_" + postfix + ".png"

        if properties.cao_export_location == '0':
            return os.path.join(
                self.get_blend_path(),
                filename
            )
        else:
            return os.path.join(
                self.get_blend_path(),
                properties.cao_export_subfolder,
                filename
            )


    def calculate_margin(self):
        """
        Calculate the margin for UVMap generation.
        """
        properties = Properties.get()
        if properties.cao_uv_map_distance_auto:
            ao = 8 * float(properties.cao_ao_margin) / float(properties.cao_ao_size)
            curv = 6 * float(properties.cao_curv_line_thickness) / float(properties.cao_curv_size)
            return ao if ao > curv else curv 
        else:
            return properties.cao_uv_map_distance


    def draw(self, context):
        prefs = PreferencesPanel.get()
        compact = prefs.compact_panels
        properties = Properties.get()
        layout = self.layout

        box = layout.box()

        if not self.get_blend_path():
            box.label(text="File not saved")
            box.label(text="Feature requires path to blend")
            return

        if properties.cao_uv_map != "__DUMMY__":
            if not compact:
                box.label(text="Export Location")

            col = box.column(align=True)
            col.row(align=True).prop(properties, "cao_export_location", expand=True)
            if properties.cao_export_location == '1':
                col.row(align=True).prop(properties, "cao_export_subfolder")
            elif properties.cao_export_location == '2':
                # TODO: Directory chooser ..
                col.row(align=True).prop(properties, "cao_export_userfolder")
            split = col.row(align=True).split(factor=0.9, align=True)
            split.prop(properties, "cao_export_map_basename")
            split.operator(UseObjectNameForMap.bl_idname, icon="URL", text="")

        if not compact:
            box = layout.box()
            box.label(text="UV Map")

        col = box.column(align=True)
        if properties.cao_uv_map != "__DUMMY__":
            col.row(align=True).prop(properties, "cao_uv_map")
        else:
            col.row().label(text="UV map required, object has none")
        col.row(align=True).prop(properties, "cao_uv_map_distance_auto", toggle=True)
        if not properties.cao_uv_map_distance_auto:
            col.row(align=True).prop(properties, "cao_uv_map_distance")
        op = col.row(align=True).operator(MapGenerateUV.bl_idname)
        op.island_margin = self.calculate_margin()

        if properties.cao_uv_map != "__DUMMY__":
            if not compact:
                box = layout.box()
                box.label(text="AO Mask")

            col = box.column(align=True)
            col.row(align=True).prop(properties, "cao_ao_size", expand=True)
            col.row(align=True).prop(properties, "cao_ao_quality")
            col.row(align=True).prop(properties, "cao_ao_distance")
            col.row(align=True).prop(properties, "cao_ao_margin")
            col.row(align=True).prop(
                properties, 
                "cao_ao_local", 
                toggle=True,
                text="Local only" if properties.cao_ao_local else "Global"
            )
            op = col.operator(BakeAoMapOperator.bl_idname)
            op.export_path = self.get_export_file("ao")
            op.name = properties.cao_export_map_basename
            op.uv_map = properties.cao_uv_map
            op.dimensions = int(properties.cao_ao_size)
            op.distance = properties.cao_ao_distance
            op.quality = properties.cao_ao_quality
            op.render_margin = properties.cao_ao_margin
            op.local = properties.cao_ao_local

            if os.path.exists(self.get_export_file("ao")):
                op = col.operator(AoNodeOperator.bl_idname)
                op.export_path = self.get_export_file("ao")
                op.name = properties.cao_export_map_basename + "_ao"
                op.uv_map = properties.cao_uv_map

            if not compact:
                box = layout.box()
                box.label(text="Curvature Mask")        

            col = box.column(align=True)
            col.row(align=True).prop(properties, "cao_curv_size", expand=True)
            col.row(align=True).prop(properties, "cao_analyze_mode", expand=True)
            col.row(align=True).prop(properties, "cao_curv_min_angle")
            col.row(align=True).prop(properties, "cao_curv_line_thickness")
            col.row(align=True).prop(properties, "cao_curv_apply_modifiers", toggle=True)
            op = col.operator(CurvatureMapOperator.bl_idname)
            op.export_path = self.get_export_file("curv")
            op.name = properties.cao_export_map_basename
            op.uv_map = properties.cao_uv_map
            op.dimensions = int(properties.cao_curv_size)
            op.analyze_mode = properties.cao_analyze_mode
            op.min_angle = properties.cao_curv_min_angle
            op.line_thickness = properties.cao_curv_line_thickness
            op.apply_modifiers = properties.cao_curv_apply_modifiers

            if os.path.exists(self.get_export_file("curv")):
                op = col.operator(CurvatureNodeOperator.bl_idname)
                op.export_path = self.get_export_file("curv")
                op.name = properties.cao_export_map_basename + "_curv"
                op.uv_map = properties.cao_uv_map


class NodeWizardExportPanel(Panel):
    """
    The panel for node wizard export (nodes space).
    """
    bl_idname = "MATERIAL_PT_assetwizard_nodewizard_export"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_label = "Node Wizard Export"
    bl_category = "Asset Wizard"  

    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'NODE_EDITOR' and \
            context.space_data.node_tree is not None and \
            context.space_data.tree_type == 'ShaderNodeTree'

    def draw(self, context):
        compact = PreferencesPanel.get().compact_panels
        properties = Properties.get()
        layout = self.layout      

        box = layout.box()
        # In case of empty asset-object-lib:
        if categories(ASSET_TYPE_MATERIAL):        
            if not compact:
                box.label(text="Asset Material Generator")

            col = box.column(align=True)
            col.row(align=True).prop(properties, "nw_new_categories")
            split = col.row(align=True).split(factor=0.9, align=True)
            split.prop(properties, "nw_new_category")
            op = split.operator(CreateCategoryOperator.bl_idname, text="", icon="ADD")
            op.asset_type = ASSET_TYPE_MATERIAL
            op.category = properties.nw_new_category
            op.top_category = properties.nw_new_categories

            col = box.column(align=True)
            col.row(align=True).prop(properties, "nw_categories")
            split = col.row(align=True).split(factor=0.5, align=True)
            op = split.operator(ExportMaterialOperator.bl_idname, icon="EXPORT")
            op.category = properties.nw_categories
            op = split.operator(ExportPBROperator.bl_idname, icon="EXPORT")
            op.add_hslbc = properties.nw_add_hslbc
            op.add_uv = properties.nw_add_uv
            op.decal = properties.nw_decal
            op.category = properties.nw_categories
        else:
            box.label(text="No material categories yet, create one")
            col = box.column(align=True)
            col.row(align=True).prop(properties, "nw_new_categories")
            split = col.row(align=True).split(factor=0.9, align=True)
            split.prop(properties, "nw_new_category")
            op = split.operator(CreateCategoryOperator.bl_idname, text="", icon="ADD")
            op.asset_type = ASSET_TYPE_MATERIAL
            op.category = properties.nw_new_category
            op.top_category = properties.nw_new_categories

