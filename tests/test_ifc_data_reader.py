"""Tests for IFC data reader tool."""

import pytest

from ifc_datareader import IfcDataReader, IfcObjectEntity, IfcSchema


class TestIfcDataReader:

    def test_ifc_datareader(self, ifc_filepath):

        # open an IFC file and access metadata
        data_reader = IfcDataReader(ifc_filepath)
        assert data_reader.filename == ifc_filepath
        # IFC schema specifications loaded from version read in file
        assert data_reader.schema_version == 'IFC2X3'
        assert isinstance(data_reader.ifc_schema, IfcSchema)
        # an IFC file must have a project description to be valid
        assert isinstance(data_reader.ifc_project, IfcObjectEntity)
        assert data_reader.ifc_project.type_name == 'IfcProject'

        assert repr(data_reader) == (
            '<{self.__class__.__name__}>('
            'filename="{self.filename}"'
            ', schema_version="{self.schema_version}"'
            ', ifc_project_name="{self.ifc_project.name}"'
            ')'.format(self=data_reader))

        # get IfcSite entities from the IFC file
        ifc_sites = data_reader.read_sites()
        assert len(ifc_sites) > 0
        for cur_ifc_site in ifc_sites:
            assert isinstance(cur_ifc_site, IfcObjectEntity)
            assert cur_ifc_site.global_id is not None
            assert cur_ifc_site.global_id == cur_ifc_site._raw.GlobalId
            # the parent of a site is expected to be a project
            assert cur_ifc_site.parent == data_reader.ifc_project
            assert cur_ifc_site.parent.info == data_reader.ifc_project.info

        # test the 'read_entity' feature
        ifc_site_entities = data_reader.read_entity('IfcSite')
        assert len(ifc_site_entities) == len(ifc_sites)
        assert ifc_site_entities == ifc_sites

        # pick a site
        ifc_site_entity = ifc_sites[0]

        # test 'parent' feature
        ifc_bld_elmt_entities = data_reader.read_entity('IfcBuildingElement')
        assert len(ifc_bld_elmt_entities) > 0
        ifc_bld_elmt_entity = ifc_bld_elmt_entities[0]
        assert isinstance(ifc_bld_elmt_entity.parent, IfcObjectEntity)
        ifc_entities = data_reader.read_entity(
            ifc_bld_elmt_entity.type_name,
            parent_entity=ifc_bld_elmt_entity.parent)
        assert len(ifc_entities) <= len(ifc_bld_elmt_entities)
        assert len(ifc_entities) > 0
        assert ifc_entities[0].parent == ifc_bld_elmt_entity.parent
        assert ifc_entities[0].parent != data_reader.ifc_project

        # test 'kids' feature
        ifc_building_entities = data_reader.read_buildings(
            parent_entity=ifc_site_entity)
        assert len(ifc_building_entities) > 0
        assert len(ifc_site_entity.kids) == len(ifc_building_entities)
        for cur_ifc_building in ifc_building_entities:
            assert cur_ifc_building.parent == ifc_site_entity

        # IfcObjectTypeEntity
        ifc_door_entities = data_reader.read_entity('IfcDoor')
        assert len(ifc_door_entities) > 0
        ifc_door_entity = ifc_door_entities[0]
        assert ifc_door_entity.object_type is not None
        assert isinstance(ifc_door_entity.object_type, IfcObjectEntity)
        assert len(ifc_door_entity.object_type.get_property_codenames()) > 0
        assert len(ifc_door_entity.property_sets) > 0
        assert len(ifc_door_entity.get_property_set_codenames()) > 0
        door_prop_codenames = ifc_door_entity.get_property_codenames()
        assert len(door_prop_codenames) > 0
        assert 'height' in door_prop_codenames
        assert ifc_door_entity.get_property_value('height') == (2110, None,)
        assert ifc_door_entity.get_property_value('width') == (910, None,)
        assert ifc_door_entity.get_property_value(
            'height', pset_codename='dimensions') == (2110, None,)

        storeys = data_reader.read_building_storeys()
        assert isinstance(storeys, tuple)
        spaces = data_reader.read_spaces()
        assert isinstance(spaces, tuple)
        zones = data_reader.read_zones()
        assert isinstance(zones, tuple)

        # errors:
        # invalid entity type
        with pytest.raises(ValueError):
            data_reader.read_entity('IfcWrongClassName')
        # invalid parent
        with pytest.raises(ValueError):
            data_reader.read_entity('IfcSite', parent_entity='bad')
        # try to find a property in an unknown property set
        assert ifc_door_entity.get_property_value(
            'height', pset_codename='unknown_pset') == (None, None,)
        # try to find a property in a wrong (but existing) property set
        assert ifc_door_entity.get_property_value(
            'height', pset_codename='identity_data') == (None, None,)
        # try to find an unknown property
        assert ifc_door_entity.get_property_value(
            'unknown_property') == (None, None,)

    @pytest.mark.parametrize(
        'ifc_filepath', ['bad_sample_test.ifc'], indirect=True)
    def test_ifc_datareader_errors(self, ifc_filepath):

        # load non existing file: value error
        with pytest.raises(ValueError):
            IfcDataReader('non_existing_file.ifc')

        # load existing file with no project entity: type error
        with pytest.raises(TypeError):
            IfcDataReader(ifc_filepath)
