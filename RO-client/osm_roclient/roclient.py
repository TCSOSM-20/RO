#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK

##
# Copyright 2015 Telefonica Investigacion y Desarrollo, S.A.U.
# This file is part of openmano
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# For those usages not covered by the Apache License, Version 2.0 please
# contact with: nfvlabs@tid.es
##

"""
openmano client used to interact with openmano-server (openmanod)
"""
__author__ = "Alfonso Tierno, Gerardo Garcia, Pablo Montes"
__date__ = "$09-oct-2014 09:09:48$"
__version__ = "0.5.0"
version_date = "2019-010-04"

from argcomplete.completers import FilesCompleter
import os
import argparse
import argcomplete
import requests
import json
import yaml
import logging
#from jsonschema import validate as js_v, exceptions as js_e


class ArgumentParserError(Exception):
    pass


class OpenmanoCLIError(Exception):
    pass


class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print("Error: {}".format(message))
        print()
        self.print_usage()
        #self.print_help()
        print()
        print("Type 'openmano -h' for help")
        raise ArgumentParserError


def config(args):
    print("OPENMANO_HOST: {}".format(mano_host))
    print("OPENMANO_PORT: {}".format(mano_port))
    if args.n:
        logger.debug("resolving tenant and datacenter names")
        mano_tenant_id = "None"
        mano_tenant_name = "None"
        mano_datacenter_id = "None"
        mano_datacenter_name = "None"
        # WIM additions
        logger.debug("resolving WIM names")
        mano_wim_id = "None"
        mano_wim_name = "None"
        try:
            mano_tenant_id = _get_item_uuid("tenants", mano_tenant)
            URLrequest = "http://{}:{}/openmano/tenants/{}".format(mano_host, mano_port, mano_tenant_id)
            mano_response = requests.get(URLrequest)
            logger.debug("openmano response: %s", mano_response.text )
            content = mano_response.json()
            mano_tenant_name = content["tenant"]["name"]
            URLrequest = "http://{}:{}/openmano/{}/datacenters/{}".format(mano_host, mano_port, mano_tenant_id,
                                                                          mano_datacenter)
            mano_response = requests.get(URLrequest)
            logger.debug("openmano response: %s", mano_response.text)
            content = mano_response.json()
            if "error" not in content:
                mano_datacenter_id = content["datacenter"]["uuid"]
                mano_datacenter_name = content["datacenter"]["name"]

            # WIM
            URLrequest = "http://{}:{}/openmano/{}/wims/{}".format(
            mano_host, mano_port, mano_tenant_id, mano_wim)
            mano_response = requests.get(URLrequest)
            logger.debug("openmano response: %s", mano_response.text)
            content = mano_response.json()
            if "error" not in content:
                mano_wim_id = content["wim"]["uuid"]
                mano_wim_name = content["wim"]["name"]

        except OpenmanoCLIError:
            pass
        print( "OPENMANO_TENANT: {}".format(mano_tenant))
        print( "    Id: {}".format(mano_tenant_id))
        print( "    Name: {}".format(mano_tenant_name))
        print( "OPENMANO_DATACENTER: {}".format(mano_datacenter))
        print( "    Id: {}".format(mano_datacenter_id))
        print( "    Name: {}".format(mano_datacenter_name))
        # WIM
        print( "OPENMANO_WIM: {}".format( (mano_wim)))
        print( "    Id: {}".format(mano_wim_id))
        print( "    Name: {}".format(mano_wim_name))

    else:
        print("OPENMANO_TENANT: {}".format(mano_tenant))
        print("OPENMANO_DATACENTER: {}".format(mano_datacenter))
        # WIM
        print("OPENMANO_WIM: {}".format(mano_wim))

def _print_verbose(mano_response, verbose_level=0):
    content = mano_response.json()
    result = 0 if mano_response.status_code==200 else mano_response.status_code
    if type(content)!=dict or len(content)!=1:
        # print("Non expected format output")
        print(str(content))
        return result

    val = next(iter(content.values()))
    if type(val)==str:
        print(val)
        return result
    elif type(val) == list:
        content_list = val
    elif type(val)==dict:
        content_list = [val]
    else:
        # print("Non expected dict/list format output"
        print(str(content))
        return result

    # print(content_list
    if verbose_level==None:
        verbose_level=0
    if verbose_level >= 3:
        print(yaml.safe_dump(content, indent=4, default_flow_style=False))
        return result

    if mano_response.status_code == 200:
        uuid = None
        for content in content_list:
            if "uuid" in content:
                uuid = content['uuid']
            elif "id" in content:
                uuid = content['id']
            elif "vim_id" in content:
                uuid = content['vim_id']
            name = content.get('name');
            if not uuid:
                uuid = ""
            if not name:
                name = ""
            myoutput = "{:38} {:20}".format(uuid, name)
            if content.get("status"):
                myoutput += " {:20}".format(content['status'])
            elif "enabled" in content and not content["enabled"]:
                myoutput += " enabled=False".ljust(20)
            if verbose_level >=1:
                if content.get('created_at'):
                    myoutput += " {:20}".format(content['created_at'])
                if content.get('sdn_attached_ports'):
                    #myoutput += " " + str(content['sdn_attached_ports']).ljust(20)
                    myoutput += "\nsdn_attached_ports:\n" + yaml.safe_dump(content['sdn_attached_ports'], indent=4, default_flow_style=False)
                if verbose_level >=2:
                    new_line='\n'
                    if content.get('type'):
                        myoutput += new_line + "  Type: {:29}".format(content['type'])
                        new_line=''
                    if content.get('description'):
                        myoutput += new_line + "  Description: {:20}".format(content['description'])
            print(myoutput)
    else:
        print(content['error']['description'])
    return result

def parser_json_yaml(file_name):
    try:
        with open(file_name, "r") as f:
            text = f.read()
    except Exception as e:
        return (False, str(e))

    #Read and parse file
    if file_name[-5:]=='.yaml' or file_name[-4:]=='.yml' or (file_name[-5:]!='.json' and '\t' not in text):
        try:
            config = yaml.load(text, Loader=yaml.SafeLoader)
        except yaml.YAMLError as exc:
            error_pos = ""
            if hasattr(exc, 'problem_mark'):
                mark = exc.problem_mark
                error_pos = " at line:{} column:{}".format(mark.line+1, mark.column+1)
            return (False, "Error loading file '"+file_name+"' yaml format error" + error_pos)
    else: #json
        try:
            config = json.loads(text)
        except Exception as e:
            return (False, "Error loading file '"+file_name+"' json format error " + str(e) )
    return True, config

def _load_file_or_yaml(content):
    '''
    'content' can be or a yaml/json file or a text containing a yaml/json text format
    This function autodetect, trying to load and parse the file,
    if fails trying to parse the 'content' text
    Returns the dictionary once parsed, or print an error and finish the program
    '''
    #Check config file exists
    if os.path.isfile(content):
        r,payload = parser_json_yaml(content)
        if not r:
            print(payload)
            exit(-1)
    elif "{" in content or ":" in content:
        try:
            payload = yaml.load(content)
        except yaml.YAMLError as exc:
            error_pos = ""
            if hasattr(exc, 'problem_mark'):
                mark = exc.problem_mark
                error_pos = " at position: ({}:{})".format(mark.line+1, mark.column+1)
            print("Error loading yaml/json text"+error_pos)
            exit (-1)
    else:
        print("'{}' is neither a valid file nor a yaml/json content".format(content))
        exit(-1)
    return payload

def _get_item_uuid(item, item_name_id, tenant=None):
    if tenant:
        URLrequest = "http://{}:{}/openmano/{}/{}".format(mano_host, mano_port, tenant, item)
    else:
        URLrequest = "http://{}:{}/openmano/{}".format(mano_host, mano_port, item)
    mano_response = requests.get(URLrequest)
    logger.debug("openmano response: %s", mano_response.text )
    content = mano_response.json()
    # print(content
    found = 0
    for i in content[item]:
        if i["uuid"] == item_name_id:
            return item_name_id
        if i["name"] == item_name_id:
            uuid = i["uuid"]
            found += 1
        if item_name_id.startswith("osm_id=") and i.get("osm_id") == item_name_id[7:]:
            uuid = i["uuid"]
            found += 1
    if found == 0:
        raise OpenmanoCLIError("No {} found with name/uuid '{}'".format(item[:-1], item_name_id))
    elif found > 1:
        raise OpenmanoCLIError("{} {} found with name '{}'. uuid must be used".format(found, item, item_name_id))
    return uuid
#
# def check_valid_uuid(uuid):
#     id_schema = {"type" : "string", "pattern": "^[a-fA-F0-9]{8}(-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}$"}
#     try:
#         js_v(uuid, id_schema)
#         return True
#     except js_e.ValidationError:
#         return False

def _get_tenant(tenant_name_id = None):
    if not tenant_name_id:
        tenant_name_id = mano_tenant
        if not mano_tenant:
            raise OpenmanoCLIError("'OPENMANO_TENANT' environment variable is not set")
    return _get_item_uuid("tenants", tenant_name_id)

def _get_datacenter(datacenter_name_id = None, tenant = "any"):
    if not datacenter_name_id:
        datacenter_name_id = mano_datacenter
        if not datacenter_name_id:
            raise OpenmanoCLIError("neither 'OPENMANO_DATACENTER' environment variable is set nor --datacenter option is used")
    return _get_item_uuid("datacenters", datacenter_name_id, tenant)

# WIM
def _get_wim(wim_name_id = None, tenant = "any"):
    if not wim_name_id:
        wim_name_id = mano_wim
        if not wim_name_id:
            raise OpenmanoCLIError("neither 'OPENMANO_WIM' environment variable is set nor --wim option is used")
    return _get_item_uuid("wims", wim_name_id, tenant)

def vnf_create(args):
    # print("vnf-create", args)
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}
    tenant = _get_tenant()
    myvnf = _load_file_or_yaml(args.file)

    api_version = ""
    if "vnfd:vnfd-catalog" in myvnf or "vnfd-catalog" in myvnf:
        api_version = "/v3"
        token = "vnfd"
        vnfd_catalog = myvnf.get("vnfd:vnfd-catalog")
        if not vnfd_catalog:
            vnfd_catalog = myvnf.get("vnfd-catalog")
        vnfds = vnfd_catalog.get("vnfd:vnfd")
        if not vnfds:
            vnfds = vnfd_catalog.get("vnfd")
        vnfd = vnfds[0]
        vdu_list = vnfd.get("vdu")

    else:  # old API
        api_version = ""
        token = "vnfs"
        vnfd = myvnf['vnf']
        vdu_list = vnfd.get("VNFC")

    if args.name or args.description or args.image_path or args.image_name or args.image_checksum:
        # TODO, change this for API v3
        # print(args.name
        try:
            if args.name:
                vnfd['name'] = args.name
            if args.description:
                vnfd['description'] = args.description
            if vdu_list:
                if args.image_path:
                    index = 0
                    for image_path_ in args.image_path.split(","):
                        # print("image-path", image_path_)
                        if api_version == "/v3":
                            if vdu_list[index].get("image"):
                                vdu_list[index]['image'] = image_path_
                                if "image-checksum" in vdu_list[index]:
                                    del vdu_list[index]["image-checksum"]
                            else:  # image name in volumes
                                vdu_list[index]["volumes"][0]["image"] = image_path_
                                if "image-checksum" in vdu_list[index]["volumes"][0]:
                                    del vdu_list[index]["volumes"][0]["image-checksum"]
                        else:
                            vdu_list[index]['VNFC image'] = image_path_
                            if "image name" in vdu_list[index]:
                                del vdu_list[index]["image name"]
                            if "image checksum" in vdu_list[index]:
                                del vdu_list[index]["image checksum"]
                        index += 1
                if args.image_name:  # image name precedes if both are supplied
                    index = 0
                    for image_name_ in args.image_name.split(","):
                        if api_version == "/v3":
                            if vdu_list[index].get("image"):
                                vdu_list[index]['image'] = image_name_
                                if "image-checksum" in vdu_list[index]:
                                    del vdu_list[index]["image-checksum"]
                                if vdu_list[index].get("alternative-images"):
                                    for a_image in vdu_list[index]["alternative-images"]:
                                        a_image['image'] = image_name_
                                        if "image-checksum" in a_image:
                                            del a_image["image-checksum"]
                            else:  # image name in volumes
                                vdu_list[index]["volumes"][0]["image"] = image_name_
                                if "image-checksum" in vdu_list[index]["volumes"][0]:
                                    del vdu_list[index]["volumes"][0]["image-checksum"]
                        else:
                            vdu_list[index]['image name'] = image_name_
                            if "VNFC image" in vdu_list[index]:
                                del vdu_list[index]["VNFC image"]
                        index += 1
                if args.image_checksum:
                    index = 0
                    for image_checksum_ in args.image_checksum.split(","):
                        if api_version == "/v3":
                            if vdu_list[index].get("image"):
                                vdu_list[index]['image-checksum'] = image_checksum_
                                if vdu_list[index].get("alternative-images"):
                                    for a_image in vdu_list[index]["alternative-images"]:
                                        a_image['image-checksum'] = image_checksum_
                            else:  # image name in volumes
                                vdu_list[index]["volumes"][0]["image-checksum"] = image_checksum_
                        else:
                            vdu_list[index]['image checksum'] = image_checksum_
                        index += 1
        except (KeyError, TypeError) as e:
            if str(e) == 'vnf':           error_pos= "missing field 'vnf'"
            elif str(e) == 'name':        error_pos= "missing field  'vnf':'name'"
            elif str(e) == 'description': error_pos= "missing field  'vnf':'description'"
            elif str(e) == 'VNFC':        error_pos= "missing field  'vnf':'VNFC'"
            elif str(e) == str(index):    error_pos= "field  'vnf':'VNFC' must be an array"
            elif str(e) == 'VNFC image':  error_pos= "missing field 'vnf':'VNFC'['VNFC image']"
            elif str(e) == 'image name':  error_pos= "missing field 'vnf':'VNFC'['image name']"
            elif str(e) == 'image checksum':  error_pos= "missing field 'vnf':'VNFC'['image checksum']"
            else:                       error_pos="wrong format"
            print("Wrong VNF descriptor: " + error_pos)
            return -1
    payload_req = json.dumps(myvnf)

    # print(payload_req

    URLrequest = "http://{}:{}/openmano{}/{}/{token}".format(mano_host, mano_port, api_version, tenant, token=token)
    logger.debug("openmano request: %s", payload_req)
    mano_response = requests.post(URLrequest, headers=headers_req, data=payload_req)
    logger.debug("openmano response: %s", mano_response.text )

    return _print_verbose(mano_response, args.verbose)

def vnf_list(args):
    # print("vnf-list",args
    if args.all:
        tenant = "any"
    else:
        tenant = _get_tenant()
    if args.name:
        toshow = _get_item_uuid("vnfs", args.name, tenant)
        URLrequest = "http://{}:{}/openmano/{}/vnfs/{}".format(mano_host, mano_port, tenant, toshow)
    else:
        URLrequest = "http://{}:{}/openmano/{}/vnfs".format(mano_host, mano_port, tenant)
    mano_response = requests.get(URLrequest)
    logger.debug("openmano response: %s", mano_response.text )
    content = mano_response.json()
    # print(json.dumps(content, indent=4)
    if args.verbose==None:
        args.verbose=0
    result = 0 if mano_response.status_code==200 else mano_response.status_code
    if mano_response.status_code == 200:
        if not args.name:
            if args.verbose >= 3:
                print(yaml.safe_dump(content, indent=4, default_flow_style=False))
                return result
            if len(content['vnfs']) == 0:
                print("No VNFs were found.")
                return 404   # HTTP_Not_Found
            for vnf in content['vnfs']:
                myoutput = "{:38} {:20}".format(vnf['uuid'], vnf['name'])
                if vnf.get('osm_id') or args.verbose >= 1:
                    myoutput += " osm_id={:20}".format(vnf.get('osm_id'))
                if args.verbose >= 1:
                    myoutput += " {}".format(vnf['created_at'])
                print(myoutput)
                if args.verbose >= 2:
                    print("  Description: {}".format(vnf['description']))
                    # print("  VNF descriptor file: {}".format(vnf['path']))
        else:
            if args.verbose:
                print(yaml.safe_dump(content, indent=4, default_flow_style=False))
                return result
            vnf = content['vnf']
            print("{:38} {:20} osm_id={:20} {:20}".format(vnf['uuid'], vnf['name'], vnf.get('osm_id'),
                                                          vnf['created_at']), end=" ")
            print("  Description: {}".format(vnf['description']))
            # print(" VNF descriptor file: {}".format(vnf['path']))
            print("  VMs:")
            for vm in vnf['VNFC']:
                print("    {:20} osm_id={:20} {}".format(vm['name'], vm.get('osm_id'), vm['description']))
            if len(vnf['nets']) > 0:
                print("  Internal nets:")
                for net in vnf['nets']:
                    print("    {:20} {}".format(net['name'], net['description']))
            if len(vnf['external-connections']) > 0:
                print("  External interfaces:")
                for interface in vnf['external-connections']:
                    print("    {:20} {:20} {:20} {:14}".format(
                        interface['external_name'], interface['vm_name'],
                        interface['internal_name'],
                        interface.get('vpci') if interface.get('vpci') else ""))
    else:
        print(content['error']['description'])
        if args.verbose:
            print(yaml.safe_dump(content, indent=4, default_flow_style=False))
    return result

def vnf_delete(args):
    # print("vnf-delete",args
    if args.all:
        tenant = "any"
    else:
        tenant = _get_tenant()
    todelete = _get_item_uuid("vnfs", args.name, tenant=tenant)
    if not args.force:
        r = input("Delete VNF {} (y/N)? ".format(todelete))
        if  not (len(r)>0  and r[0].lower()=="y"):
            return 0
    URLrequest = "http://{}:{}/openmano/{}/vnfs/{}".format(mano_host, mano_port, tenant, todelete)
    mano_response = requests.delete(URLrequest)
    logger.debug("openmano response: %s", mano_response.text )
    result = 0 if mano_response.status_code==200 else mano_response.status_code
    content = mano_response.json()
    # print(json.dumps(content, indent=4))
    if mano_response.status_code == 200:
        print(content['result'])
    else:
        print(content['error']['description'])
    return result

def scenario_create(args):
    # print("scenario-create",args
    tenant = _get_tenant()
    headers_req = {'content-type': 'application/yaml'}
    myscenario = _load_file_or_yaml(args.file)
    if "nsd:nsd-catalog" in myscenario or "nsd-catalog" in myscenario:
        api_version = "/v3"
        token = "nsd"
        nsd_catalog = myscenario.get("nsd:nsd-catalog")
        if not nsd_catalog:
            nsd_catalog = myscenario.get("nsd-catalog")
        nsds = nsd_catalog.get("nsd:nsd")
        if not nsds:
            nsds = nsd_catalog.get("nsd")
        nsd = nsds[0]
    else:  # API<v3
        api_version = ""
        token = "scenarios"
        if "scenario" in myscenario:
            nsd = myscenario["scenario"]
        else:
            nsd = myscenario
    # TODO modify for API v3
    if args.name:
        nsd['name'] = args.name
    if args.description:
        nsd['description'] = args.description
    payload_req = yaml.safe_dump(myscenario, explicit_start=True, indent=4, default_flow_style=False, tags=False,
                                 allow_unicode=True)

    # print(payload_req
    URLrequest = "http://{host}:{port}/openmano{api}/{tenant}/{token}".format(
        host=mano_host, port=mano_port, api=api_version, tenant=tenant, token=token)
    logger.debug("openmano request: %s", payload_req)
    mano_response = requests.post(URLrequest, headers = headers_req, data=payload_req)
    logger.debug("openmano response: %s", mano_response.text )
    return _print_verbose(mano_response, args.verbose)

def scenario_list(args):
    # print("scenario-list",args
    if args.all:
        tenant = "any"
    else:
        tenant = _get_tenant()
    if args.name:
        toshow = _get_item_uuid("scenarios", args.name, tenant)
        URLrequest = "http://{}:{}/openmano/{}/scenarios/{}".format(mano_host, mano_port, tenant, toshow)
    else:
        URLrequest = "http://{}:{}/openmano/{}/scenarios".format(mano_host, mano_port, tenant)
    mano_response = requests.get(URLrequest)
    logger.debug("openmano response: %s", mano_response.text )
    content = mano_response.json()
    # print(json.dumps(content, indent=4)
    if args.verbose==None:
        args.verbose=0

    result = 0 if mano_response.status_code==200 else mano_response.status_code
    if mano_response.status_code == 200:
        if not args.name:
            if args.verbose >= 3:
                print( yaml.safe_dump(content, indent=4, default_flow_style=False))
                return result
            if len(content['scenarios']) == 0:
                print( "No scenarios were found.")
                return 404 #HTTP_Not_Found
            for scenario in content['scenarios']:
                myoutput = "{:38} {:20}".format(scenario['uuid'], scenario['name'])
                if scenario.get('osm_id') or args.verbose >= 1:
                    myoutput += " osm_id={:20}".format(scenario.get('osm_id'))
                if args.verbose >= 1:
                    myoutput += " {}".format(scenario['created_at'])
                print(myoutput)
                if args.verbose >=2:
                    print("  Description: {}".format(scenario['description']))
        else:
            if args.verbose:
                print(yaml.safe_dump(content, indent=4, default_flow_style=False))
                return result
            scenario = content['scenario']
            print("{:38} {:20} osm_id={:20} {:20}".format(scenario['uuid'], scenario['name'], scenario.get('osm_id'),
                                                          scenario['created_at']), end=" ")
            print("  Description: {}".format(scenario['description']))
            print("  VNFs:")
            for vnf in scenario['vnfs']:
                print("    {:38} {:20} vnf_index={} {}".format(vnf['vnf_id'], vnf['name'], vnf.get("member_vnf_index"),
                                                                vnf['description']))
            if len(scenario['nets']) > 0:
                print("  nets:")
                for net in scenario['nets']:
                    description = net['description']
                    if not description:   # if description does not exist, description is "-". Valid for external and internal nets.
                        description = '-'
                    vim_id = ""
                    if net.get('vim_id'):
                        vim_id = " vim_id=" + net["vim_id"]
                    external = ""
                    if net["external"]:
                        external = " external"
                    print("    {:20} {:38} {:30}{}{}".format(net['name'], net['uuid'], description, vim_id, external))
    else:
        print(content['error']['description'])
        if args.verbose:
            print(yaml.safe_dump(content, indent=4, default_flow_style=False))
    return result

def scenario_delete(args):
    # print("scenario-delete",args
    if args.all:
        tenant = "any"
    else:
        tenant = _get_tenant()
    todelete = _get_item_uuid("scenarios", args.name, tenant=tenant)
    if not args.force:
        r = input("Delete scenario {} (y/N)? ".format(args.name))
        if  not (len(r)>0  and r[0].lower()=="y"):
            return 0
    URLrequest = "http://{}:{}/openmano/{}/scenarios/{}".format(mano_host, mano_port, tenant, todelete)
    mano_response = requests.delete(URLrequest)
    logger.debug("openmano response: %s", mano_response.text )
    result = 0 if mano_response.status_code==200 else mano_response.status_code
    content = mano_response.json()
    # print(json.dumps(content, indent=4)
    if mano_response.status_code == 200:
        print( content['result'])
    else:
        print( content['error']['description'])
    return result

def scenario_deploy(args):
    print("This command is deprecated, use 'openmano instance-scenario-create --scenario {} --name {}' instead!!!".format(args.scenario, args.name))
    print()
    args.file = None
    args.netmap_use = None
    args.netmap_create = None
    args.keypair = None
    args.keypair_auto = None
    return instance_create(args)

#     # print("scenario-deploy",args
#     headers_req = {'content-type': 'application/json'}
#     action = {}
#     actionCmd="start"
#     if args.nostart:
#         actionCmd="reserve"
#     action[actionCmd] = {}
#     action[actionCmd]["instance_name"] = args.name
#     if args.datacenter != None:
#         action[actionCmd]["datacenter"] = args.datacenter
#     elif mano_datacenter != None:
#         action[actionCmd]["datacenter"] = mano_datacenter
#
#     if args.description:
#         action[actionCmd]["description"] = args.description
#     payload_req = json.dumps(action, indent=4)
#     # print(payload_req
#
#     URLrequest = "http://{}:{}/openmano/{}/scenarios/{}/action".format(mano_host, mano_port, mano_tenant, args.scenario)
#     logger.debug("openmano request: %s", payload_req)
#     mano_response = requests.post(URLrequest, headers = headers_req, data=payload_req)
#     logger.debug("openmano response: %s", mano_response.text )
#     if args.verbose==None:
#         args.verbose=0
#
#     result = 0 if mano_response.status_code==200 else mano_response.status_code
#     content = mano_response.json()
#     # print(json.dumps(content, indent=4))
#     if args.verbose >= 3:
#         print(yaml.safe_dump(content, indent=4, default_flow_style=False))
#         return result
#
#     if mano_response.status_code == 200:
#         myoutput = "{} {}".format(content['uuid'].ljust(38),content['name'].ljust(20))
#         if args.verbose >=1:
#             myoutput = "{} {}".format(myoutput, content['created_at'].ljust(20))
#         if args.verbose >=2:
#             myoutput = "{} {} {}".format(myoutput, content['description'].ljust(30))
#         print(myoutput)
#         print("")
#         print("To check the status, run the following command:")
#         print("openmano instance-scenario-list <instance_id>"
#     else:
#         print(content['error']['description'])
#     return result

def scenario_verify(args):
    # print("scenario-verify",args)
    tenant = _get_tenant()
    headers_req = {'content-type': 'application/json'}
    action = {}
    action["verify"] = {}
    action["verify"]["instance_name"] = "scen-verify-return5"
    payload_req = json.dumps(action, indent=4)
    # print(payload_req)

    URLrequest = "http://{}:{}/openmano/{}/scenarios/{}/action".format(mano_host, mano_port, tenant, args.scenario)
    logger.debug("openmano request: %s", payload_req)
    mano_response = requests.post(URLrequest, headers = headers_req, data=payload_req)
    logger.debug("openmano response: %s", mano_response.text )

    result = 0 if mano_response.status_code==200 else mano_response.status_code
    content = mano_response.json()
    # print(json.dumps(content, indent=4))
    if mano_response.status_code == 200:
        print(content['result'])
    else:
        print(content['error']['description'])
    return result

def instance_create(args):
    tenant = _get_tenant()
    headers_req = {'content-type': 'application/yaml'}
    myInstance={"instance": {}, "schema_version": "0.1"}
    if args.file:
        instance_dict = _load_file_or_yaml(args.file)
        if "instance" not in instance_dict:
            myInstance = {"instance": instance_dict, "schema_version": "0.1"}
        else:
            myInstance = instance_dict
    if args.name:
        myInstance["instance"]['name'] = args.name
    if args.description:
        myInstance["instance"]['description'] = args.description
    if args.nostart:
        myInstance["instance"]['action'] = "reserve"
    #datacenter
    datacenter = myInstance["instance"].get("datacenter")
    if args.datacenter != None:
        datacenter = args.datacenter
    myInstance["instance"]["datacenter"] = _get_datacenter(datacenter, tenant)
    #scenario
    scenario = myInstance["instance"].get("scenario")
    if args.scenario != None:
        scenario = args.scenario
    if not scenario:
        print("you must provide a scenario in the file descriptor or with --scenario")
        return -1
    if isinstance(scenario, str):
        myInstance["instance"]["scenario"] = _get_item_uuid("scenarios", scenario, tenant)
    if args.netmap_use:
        if "networks" not in myInstance["instance"]:
            myInstance["instance"]["networks"] = {}
        for net in args.netmap_use:
            net_comma_list = net.split(",")
            for net_comma in net_comma_list:
                net_tuple = net_comma.split("=")
                if len(net_tuple) != 2:
                    print("error at netmap-use. Expected net-scenario=net-datacenter. ({})?".format(net_comma))
                    return
                net_scenario   = net_tuple[0].strip()
                net_datacenter = net_tuple[1].strip()
                if net_scenario not in myInstance["instance"]["networks"]:
                    myInstance["instance"]["networks"][net_scenario] = {}
                if "sites" not in myInstance["instance"]["networks"][net_scenario]:
                    myInstance["instance"]["networks"][net_scenario]["sites"] = [ {} ]
                myInstance["instance"]["networks"][net_scenario]["sites"][0]["netmap-use"] = net_datacenter
    if args.netmap_create:
        if "networks" not in myInstance["instance"]:
            myInstance["instance"]["networks"] = {}
        for net in args.netmap_create:
            net_comma_list = net.split(",")
            for net_comma in net_comma_list:
                net_tuple = net_comma.split("=")
                if len(net_tuple) == 1:
                    net_scenario   = net_tuple[0].strip()
                    net_datacenter = None
                elif len(net_tuple) == 2:
                    net_scenario   = net_tuple[0].strip()
                    net_datacenter = net_tuple[1].strip()
                else:
                    print("error at netmap-create. Expected net-scenario=net-datacenter or net-scenario. ({})?".format(
                        net_comma))
                    return
                if net_scenario not in myInstance["instance"]["networks"]:
                    myInstance["instance"]["networks"][net_scenario] = {}
                if "sites" not in myInstance["instance"]["networks"][net_scenario]:
                    myInstance["instance"]["networks"][net_scenario]["sites"] = [ {} ]
                myInstance["instance"]["networks"][net_scenario]["sites"][0]["netmap-create"] = net_datacenter
    if args.keypair:
        if "cloud-config" not in myInstance["instance"]:
            myInstance["instance"]["cloud-config"] = {}
        cloud_config = myInstance["instance"]["cloud-config"]
        for key in args.keypair:
            index = key.find(":")
            if index<0:
                if "key-pairs" not in cloud_config:
                    cloud_config["key-pairs"] = []
                cloud_config["key-pairs"].append(key)
            else:
                user = key[:index]
                key_ = key[index+1:]
                key_list = key_.split(",")
                if "users" not in cloud_config:
                    cloud_config["users"] = []
                cloud_config["users"].append({"name": user, "key-pairs": key_list  })
    if args.keypair_auto:
        try:
            keys=[]
            home = os.getenv("HOME")
            user = os.getenv("USER")
            files = os.listdir(home+'/.ssh')
            for file in files:
                if file[-4:] == ".pub":
                    with open(home+'/.ssh/'+file, 'r') as f:
                        keys.append(f.read())
            if not keys:
                print("Cannot obtain any public ssh key from '{}'. Try not using --keymap-auto".format(home+'/.ssh'))
                return 1
        except Exception as e:
            print("Cannot obtain any public ssh key. Error '{}'. Try not using --keymap-auto".format(str(e)))
            return 1

        if "cloud-config" not in myInstance["instance"]:
            myInstance["instance"]["cloud-config"] = {}
        cloud_config = myInstance["instance"]["cloud-config"]
        if "key-pairs" not in cloud_config:
            cloud_config["key-pairs"] = []
        if user:
            if "users" not in cloud_config:
                cloud_config["users"] = []
            cloud_config["users"].append({"name": user, "key-pairs": keys })

    payload_req = yaml.safe_dump(myInstance, explicit_start=True, indent=4, default_flow_style=False, tags=False,
                                 allow_unicode=True)
    logger.debug("openmano request: %s", payload_req)
    URLrequest = "http://{}:{}/openmano/{}/instances".format(mano_host, mano_port, tenant)
    mano_response = requests.post(URLrequest, headers = headers_req, data=payload_req)
    logger.debug("openmano response: %s", mano_response.text )
    if args.verbose==None:
        args.verbose=0

    result = 0 if mano_response.status_code==200 else mano_response.status_code
    content = mano_response.json()
    # print(json.dumps(content, indent=4))
    if args.verbose >= 3:
        print(yaml.safe_dump(content, indent=4, default_flow_style=False))
        return result

    if mano_response.status_code == 200:
        myoutput = "{:38} {:20}".format(content['uuid'], content['name'])
        if args.verbose >=1:
            myoutput = "{} {:20}".format(myoutput, content['created_at'])
        if args.verbose >=2:
            myoutput = "{} {:30}".format(myoutput, content['description'])
        print(myoutput)
    else:
        print(content['error']['description'])
    return result

def instance_scenario_list(args):
    # print("instance-scenario-list",args)
    if args.all:
        tenant = "any"
    else:
        tenant = _get_tenant()
    if args.name:
        toshow = _get_item_uuid("instances", args.name, tenant)
        URLrequest = "http://{}:{}/openmano/{}/instances/{}".format(mano_host, mano_port, tenant, toshow)
    else:
        URLrequest = "http://{}:{}/openmano/{}/instances".format(mano_host, mano_port, tenant)
    mano_response = requests.get(URLrequest)
    logger.debug("openmano response: %s", mano_response.text )
    content = mano_response.json()
    # print(json.dumps(content, indent=4)
    if args.verbose==None:
        args.verbose=0

    result = 0 if mano_response.status_code==200 else mano_response.status_code
    if mano_response.status_code == 200:
        if not args.name:
            if args.verbose >= 3:
                print(yaml.safe_dump(content, indent=4, default_flow_style=False))
                return result
            if len(content['instances']) == 0:
                print("No scenario instances were found.")
                return result
            for instance in content['instances']:
                myoutput = "{:38} {:20}".format(instance['uuid'], instance['name'])
                if args.verbose >=1:
                    myoutput = "{} {:20}".format(myoutput, instance['created_at'])
                print(myoutput)
                if args.verbose >=2:
                    print("Description: {}".format(instance['description']))
        else:
            if args.verbose:
                print(yaml.safe_dump(content, indent=4, default_flow_style=False))
                return result
            instance = content
            print("{:38} {:20} {:20}".format(instance['uuid'],instance['name'],instance['created_at']))
            print("Description: {}".format(instance['description']))
            print("Template scenario id: {}".format(instance['scenario_id']))
            print("Template scenario name: {}".format(instance['scenario_name']))
            print("---------------------------------------")
            print("VNF instances: {}".format(len(instance['vnfs'])))
            for vnf in instance['vnfs']:
                # print("    {} {} Template vnf name: {} Template vnf id: {}".format(vnf['uuid'].ljust(38), vnf['name'].ljust(20), vnf['vnf_name'].ljust(20), vnf['vnf_id'].ljust(38))
                print("    {:38} {:20} Template vnf id: {:38}".format(vnf['uuid'], vnf['vnf_name'], vnf['vnf_id']))
            if len(instance['nets'])>0:
                print("---------------------------------------")
                print("Internal nets:")
                for net in instance['nets']:
                    if net['created']:
                        print("    {:38} {:12} VIM ID: {}".format(net['uuid'], net['status'], net['vim_net_id']))
                print("---------------------------------------")
                print("External nets:")
                for net in instance['nets']:
                    if not net['created']:
                        print("    {:38} {:12} VIM ID: {}".format(net['uuid'], net['status'], net['vim_net_id']))
            print("---------------------------------------")
            print("VM instances:")
            for vnf in instance['vnfs']:
                for vm in vnf['vms']:
                    print("    {:38} {:20} {:20} {:12} VIM ID: {}".format(vm['uuid'], vnf['vnf_name'], vm['name'],
                                                                          vm['status'], vm['vim_vm_id']))
    else:
        print(content['error']['description'])
        if args.verbose:
            print(yaml.safe_dump(content, indent=4, default_flow_style=False))
    return result

def instance_scenario_status(args):
    print("instance-scenario-status")
    return 0

def instance_scenario_delete(args):
    if args.all:
        tenant = "any"
    else:
        tenant = _get_tenant()
    todelete = _get_item_uuid("instances", args.name, tenant=tenant)
    # print("instance-scenario-delete",args)
    if not args.force:
        r = input("Delete scenario instance {} (y/N)? ".format(args.name))
        if  not (len(r)>0  and r[0].lower()=="y"):
            return
    URLrequest = "http://{}:{}/openmano/{}/instances/{}".format(mano_host, mano_port, tenant, todelete)
    mano_response = requests.delete(URLrequest)
    logger.debug("openmano response: %s", mano_response.text )
    result = 0 if mano_response.status_code==200 else mano_response.status_code
    content = mano_response.json()
    # print(json.dumps(content, indent=4))
    if mano_response.status_code == 200:
        print(content['result'])
    else:
        print(content['error']['description'])
    return result

def get_action(args):
    if not args.all:
        tenant = _get_tenant()
    else:
        tenant = "any"
    if not args.instance:
        instance_id = "any"
    else:
        instance_id =args.instance
    action_id = ""
    if args.id:
        action_id = "/" + args.id
    URLrequest = "http://{}:{}/openmano/{}/instances/{}/action{}".format(mano_host, mano_port, tenant, instance_id,
                                                                         action_id)
    mano_response = requests.get(URLrequest)
    logger.debug("openmano response: %s", mano_response.text )
    if args.verbose == None:
        args.verbose = 0
    if args.id != None:
        args.verbose += 1
    return _print_verbose(mano_response, args.verbose)

def instance_scenario_action(args):
    # print("instance-scenario-action", args)
    tenant = _get_tenant()
    toact = _get_item_uuid("instances", args.name, tenant=tenant)
    action={}
    action[ args.action ] = yaml.safe_load(args.param)
    if args.vnf:
        action["vnfs"] = args.vnf
    if args.vm:
        action["vms"] = args.vm

    headers_req = {'content-type': 'application/json'}
    payload_req = json.dumps(action, indent=4)
    URLrequest = "http://{}:{}/openmano/{}/instances/{}/action".format(mano_host, mano_port, tenant, toact)
    logger.debug("openmano request: %s", payload_req)
    mano_response = requests.post(URLrequest, headers = headers_req, data=payload_req)
    logger.debug("openmano response: %s", mano_response.text )
    result = 0 if mano_response.status_code==200 else mano_response.status_code
    content = mano_response.json()
    # print(json.dumps(content, indent=4))
    if mano_response.status_code == 200:
        if args.verbose:
            print(yaml.safe_dump(content, indent=4, default_flow_style=False))
            return result
        if "instance_action_id" in content:
            print("instance_action_id={}".format(content["instance_action_id"]))
        else:
            for uuid,c in content.items():
                print("{:38} {:20} {:20}".format(uuid, c.get('name'), c.get('description')))
    else:
        print(content['error']['description'])
    return result


def instance_vnf_list(args):
    print("instance-vnf-list")
    return 0

def instance_vnf_status(args):
    print("instance-vnf-status")
    return 0

def tenant_create(args):
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}
    tenant_dict={"name": args.name}
    if args.description!=None:
        tenant_dict["description"] = args.description
    payload_req = json.dumps( {"tenant": tenant_dict })

    # print(payload_req)

    URLrequest = "http://{}:{}/openmano/tenants".format(mano_host, mano_port)
    logger.debug("openmano request: %s", payload_req)
    mano_response = requests.post(URLrequest, headers=headers_req, data=payload_req)
    logger.debug("openmano response: %s", mano_response.text )
    return _print_verbose(mano_response, args.verbose)

def tenant_list(args):
    # print("tenant-list",args)
    if args.name:
        toshow = _get_item_uuid("tenants", args.name)
        URLrequest = "http://{}:{}/openmano/tenants/{}".format(mano_host, mano_port, toshow)
    else:
        URLrequest = "http://{}:{}/openmano/tenants".format(mano_host, mano_port)
    mano_response = requests.get(URLrequest)
    logger.debug("openmano response: %s", mano_response.text )
    if args.verbose==None:
        args.verbose=0
    if args.name!=None:
        args.verbose += 1
    return _print_verbose(mano_response, args.verbose)

def tenant_delete(args):
    # print("tenant-delete",args)
    todelete = _get_item_uuid("tenants", args.name)
    if not args.force:
        r = input("Delete tenant {} (y/N)? ".format(args.name))
        if  not (len(r)>0  and r[0].lower()=="y"):
            return 0
    URLrequest = "http://{}:{}/openmano/tenants/{}".format(mano_host, mano_port, todelete)
    mano_response = requests.delete(URLrequest)
    logger.debug("openmano response: %s", mano_response.text )
    result = 0 if mano_response.status_code==200 else mano_response.status_code
    content = mano_response.json()
    # print(json.dumps(content, indent=4))
    if mano_response.status_code == 200:
        print(content['result'])
    else:
        print(content['error']['description'])
    return result

def datacenter_attach(args):
    tenant = _get_tenant()
    datacenter = _get_datacenter(args.name)
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}

    datacenter_dict={}
    if args.vim_tenant_id != None:
        datacenter_dict['vim_tenant'] = args.vim_tenant_id
    if args.vim_tenant_name != None:
        datacenter_dict['vim_tenant_name'] = args.vim_tenant_name
    if args.user != None:
        datacenter_dict['vim_username'] = args.user
    if args.password != None:
        datacenter_dict['vim_password'] = args.password
    if args.config!=None:
        datacenter_dict["config"] = _load_file_or_yaml(args.config)

    payload_req = json.dumps( {"datacenter": datacenter_dict })

    # print(payload_req)

    URLrequest = "http://{}:{}/openmano/{}/datacenters/{}".format(mano_host, mano_port, tenant, datacenter)
    logger.debug("openmano request: %s", payload_req)
    mano_response = requests.post(URLrequest, headers=headers_req, data=payload_req)
    logger.debug("openmano response: %s", mano_response.text )
    result = _print_verbose(mano_response, args.verbose)
    #provide addional information if error
    if mano_response.status_code != 200:
        content = mano_response.json()
        if "already in use for  'name'" in content['error']['description'] and \
                "to database vim_tenants table" in content['error']['description']:
            print("Try to specify a different name with --vim-tenant-name")
    return result


def datacenter_edit_vim_tenant(args):
    tenant = _get_tenant()
    datacenter = _get_datacenter(args.name)
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}

    if not (args.vim_tenant_id or args.vim_tenant_name or args.user or args.password or args.config):
        raise OpenmanoCLIError("Error. At least one parameter must be updated.")

    datacenter_dict = {}
    if args.vim_tenant_id != None:
        datacenter_dict['vim_tenant'] = args.vim_tenant_id
    if args.vim_tenant_name != None:
        datacenter_dict['vim_tenant_name'] = args.vim_tenant_name
    if args.user != None:
        datacenter_dict['vim_username'] = args.user
    if args.password != None:
        datacenter_dict['vim_password'] = args.password
    if args.config != None:
        datacenter_dict["config"] = _load_file_or_yaml(args.config)
    payload_req = json.dumps({"datacenter": datacenter_dict})

    # print(payload_req)

    URLrequest = "http://{}:{}/openmano/{}/datacenters/{}".format(mano_host, mano_port, tenant, datacenter)
    logger.debug("openmano request: %s", payload_req)
    mano_response = requests.put(URLrequest, headers=headers_req, data=payload_req)
    logger.debug("openmano response: %s", mano_response.text)
    result = _print_verbose(mano_response, args.verbose)

    return result

def datacenter_detach(args):
    if args.all:
        tenant = "any"
    else:
        tenant = _get_tenant()
    datacenter = _get_datacenter(args.name, tenant)
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}
    URLrequest = "http://{}:{}/openmano/{}/datacenters/{}".format(mano_host, mano_port, tenant, datacenter)
    mano_response = requests.delete(URLrequest, headers=headers_req)
    logger.debug("openmano response: %s", mano_response.text )
    content = mano_response.json()
    # print(json.dumps(content, indent=4))
    result = 0 if mano_response.status_code==200 else mano_response.status_code
    if mano_response.status_code == 200:
        print(content['result'])
    else:
        print(content['error']['description'])
    return result

def datacenter_create(args):
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}
    datacenter_dict={"name": args.name, "vim_url": args.url}
    if args.description!=None:
        datacenter_dict["description"] = args.description
    if args.type!=None:
        datacenter_dict["type"] = args.type
    if args.url!=None:
        datacenter_dict["vim_url_admin"] = args.url_admin
    if args.config!=None:
        datacenter_dict["config"] = _load_file_or_yaml(args.config)
    if args.sdn_controller!=None:
        tenant = _get_tenant()
        sdn_controller = _get_item_uuid("sdn_controllers", args.sdn_controller, tenant)
        if not 'config' in datacenter_dict:
            datacenter_dict['config'] = {}
        datacenter_dict['config']['sdn-controller'] = sdn_controller
    payload_req = json.dumps( {"datacenter": datacenter_dict })

    # print(payload_req)

    URLrequest = "http://{}:{}/openmano/datacenters".format(mano_host, mano_port)
    logger.debug("openmano request: %s", payload_req)
    mano_response = requests.post(URLrequest, headers=headers_req, data=payload_req)
    logger.debug("openmano response: %s", mano_response.text )
    return _print_verbose(mano_response, args.verbose)

def datacenter_delete(args):
    # print("datacenter-delete",args)
    todelete = _get_item_uuid("datacenters", args.name, "any")
    if not args.force:
        r = input("Delete datacenter {} (y/N)? ".format(args.name))
        if  not (len(r)>0  and r[0].lower()=="y"):
            return 0
    URLrequest = "http://{}:{}/openmano/datacenters/{}".format(mano_host, mano_port, todelete)
    mano_response = requests.delete(URLrequest)
    logger.debug("openmano response: %s", mano_response.text )
    result = 0 if mano_response.status_code==200 else mano_response.status_code
    content = mano_response.json()
    # print(json.dumps(content, indent=4))
    if mano_response.status_code == 200:
        print(content['result'])
    else:
        print(content['error']['description'])
    return result


def datacenter_list(args):
    # print("datacenter-list",args)
    tenant='any' if args.all else _get_tenant()

    if args.name:
        toshow = _get_item_uuid("datacenters", args.name, tenant)
        URLrequest = "http://{}:{}/openmano/{}/datacenters/{}".format(mano_host, mano_port, tenant, toshow)
    else:
        URLrequest = "http://{}:{}/openmano/{}/datacenters".format(mano_host, mano_port, tenant)
    mano_response = requests.get(URLrequest)
    logger.debug("openmano response: %s", mano_response.text )
    if args.verbose==None:
        args.verbose=0
    if args.name!=None:
        args.verbose += 1
    return _print_verbose(mano_response, args.verbose)


def datacenter_sdn_port_mapping_set(args):
    tenant = _get_tenant()
    datacenter = _get_datacenter(args.name, tenant)
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}

    if not args.file:
        raise OpenmanoCLIError(
            "No yaml/json has been provided specifying the SDN port mapping")
    sdn_port_mapping = _load_file_or_yaml(args.file)
    payload_req = json.dumps({"sdn_port_mapping": sdn_port_mapping})

    # read
    URLrequest = "http://{}:{}/openmano/{}/datacenters/{}/sdn_mapping".format(mano_host, mano_port, tenant, datacenter)
    mano_response = requests.get(URLrequest)
    logger.debug("openmano response: %s", mano_response.text)
    port_mapping = mano_response.json()
    if mano_response.status_code != 200:
        str(mano_response.json())
        raise OpenmanoCLIError("openmano client error: {}".format(port_mapping['error']['description']))
    if len(port_mapping["sdn_port_mapping"]["ports_mapping"]) > 0:
        if not args.force:
            r = input("Datacenter {} already contains a port mapping. Overwrite? (y/N)? ".format(datacenter))
            if not (len(r) > 0 and r[0].lower() == "y"):
                return 0

        # clear
        URLrequest = "http://{}:{}/openmano/{}/datacenters/{}/sdn_mapping".format(mano_host, mano_port, tenant, datacenter)
        mano_response = requests.delete(URLrequest)
        logger.debug("openmano response: %s", mano_response.text)
        if mano_response.status_code != 200:
            return _print_verbose(mano_response, args.verbose)

    # set
    URLrequest = "http://{}:{}/openmano/{}/datacenters/{}/sdn_mapping".format(mano_host, mano_port, tenant, datacenter)
    logger.debug("openmano request: %s", payload_req)
    mano_response = requests.post(URLrequest, headers=headers_req, data=payload_req)
    logger.debug("openmano response: %s", mano_response.text)
    return _print_verbose(mano_response, args.verbose)


def datacenter_sdn_port_mapping_list(args):
    tenant = _get_tenant()
    datacenter = _get_datacenter(args.name, tenant)

    URLrequest = "http://{}:{}/openmano/{}/datacenters/{}/sdn_mapping".format(mano_host, mano_port, tenant, datacenter)
    mano_response = requests.get(URLrequest)
    logger.debug("openmano response: %s", mano_response.text)

    return _print_verbose(mano_response, 4)


def datacenter_sdn_port_mapping_clear(args):
    tenant = _get_tenant()
    datacenter = _get_datacenter(args.name, tenant)

    if not args.force:
        r = input("Clean SDN port mapping for datacenter {} (y/N)? ".format(datacenter))
        if not (len(r) > 0 and r[0].lower() == "y"):
            return 0

    URLrequest = "http://{}:{}/openmano/{}/datacenters/{}/sdn_mapping".format(mano_host, mano_port, tenant, datacenter)
    mano_response = requests.delete(URLrequest)
    logger.debug("openmano response: %s", mano_response.text)

    return _print_verbose(mano_response, args.verbose)


def sdn_controller_create(args):
    tenant = _get_tenant()
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}

    error_msg=[]
    if not args.ip: error_msg.append("'ip'")
    if not args.port: error_msg.append("'port'")
    if not args.dpid: error_msg.append("'dpid'")
    if not args.type: error_msg.append("'type'")
    if error_msg:
        raise OpenmanoCLIError("The following arguments are required: " + ",".join(error_msg))

    controller_dict = {}
    controller_dict['name'] = args.name
    controller_dict['ip'] = args.ip
    controller_dict['port'] = int(args.port)
    controller_dict['dpid'] = args.dpid
    controller_dict['type'] = args.type
    if args.description != None:
        controller_dict['description'] = args.description
    if args.user != None:
        controller_dict['user'] = args.user
    if args.password != None:
        controller_dict['password'] = args.password

    payload_req = json.dumps({"sdn_controller": controller_dict})

    # print(payload_req)

    URLrequest = "http://{}:{}/openmano/{}/sdn_controllers".format(mano_host, mano_port, tenant)
    logger.debug("openmano request: %s", payload_req)
    mano_response = requests.post(URLrequest, headers=headers_req, data=payload_req)
    logger.debug("openmano response: %s", mano_response.text)
    result = _print_verbose(mano_response, args.verbose)
    return result


def sdn_controller_edit(args):
    tenant = _get_tenant()
    controller_uuid = _get_item_uuid("sdn_controllers", args.name, tenant)
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}

    controller_dict = {}
    if args.new_name:
        controller_dict['name'] = args.new_name
    if args.ip:
        controller_dict['ip'] = args.ip
    if args.port:
        controller_dict['port'] = int(args.port)
    if args.dpid:
        controller_dict['dpid'] = args.dpid
    if args.type:
        controller_dict['type'] = args.type
    if args.description:
        controller_dict['description'] = args.description
    if args.user:
        controller_dict['user'] = args.user
    if args.password:
        controller_dict['password'] = args.password

    if not controller_dict:
        raise OpenmanoCLIError("At least one parameter must be edited")

    if not args.force:
        r = input("Update SDN controller {} (y/N)? ".format(args.name))
        if not (len(r) > 0 and r[0].lower() == "y"):
            return 0

    payload_req = json.dumps({"sdn_controller": controller_dict})
    # print(payload_req)

    URLrequest = "http://{}:{}/openmano/{}/sdn_controllers/{}".format(mano_host, mano_port, tenant, controller_uuid)
    logger.debug("openmano request: %s", payload_req)
    mano_response = requests.put(URLrequest, headers=headers_req, data=payload_req)
    logger.debug("openmano response: %s", mano_response.text)
    result = _print_verbose(mano_response, args.verbose)
    return result


def sdn_controller_list(args):
    tenant = _get_tenant()
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}

    if args.name:
        toshow = _get_item_uuid("sdn_controllers", args.name, tenant)
        URLrequest = "http://{}:{}/openmano/{}/sdn_controllers/{}".format(mano_host, mano_port, tenant, toshow)
    else:
        URLrequest = "http://{}:{}/openmano/{}/sdn_controllers".format(mano_host, mano_port, tenant)
    # print(URLrequest)
    mano_response = requests.get(URLrequest)
    logger.debug("openmano response: %s", mano_response.text )
    if args.verbose==None:
        args.verbose=0
    if args.name!=None:
        args.verbose += 1

    # json.dumps(mano_response.json(), indent=4)
    return _print_verbose(mano_response, args.verbose)


def sdn_controller_delete(args):
    tenant = _get_tenant()
    controller_uuid = _get_item_uuid("sdn_controllers", args.name, tenant)

    if not args.force:
        r = input("Delete SDN controller {} (y/N)? ".format(args.name))
        if not (len(r) > 0 and r[0].lower() == "y"):
            return 0

    URLrequest = "http://{}:{}/openmano/{}/sdn_controllers/{}".format(mano_host, mano_port, tenant, controller_uuid)
    mano_response = requests.delete(URLrequest)
    logger.debug("openmano response: %s", mano_response.text)
    return _print_verbose(mano_response, args.verbose)

def vim_action(args):
    # print("datacenter-net-action",args)
    tenant = _get_tenant()
    datacenter = _get_datacenter(args.datacenter, tenant)
    if args.verbose==None:
        args.verbose=0
    if args.action=="list":
        URLrequest = "http://{}:{}/openmano/{}/vim/{}/{}s".format(mano_host, mano_port, tenant, datacenter, args.item)
        if args.name!=None:
            args.verbose += 1
            URLrequest += "/" + args.name
        mano_response = requests.get(URLrequest)
        logger.debug("openmano response: %s", mano_response.text )
        return _print_verbose(mano_response, args.verbose)
    elif args.action=="delete":
        URLrequest = "http://{}:{}/openmano/{}/vim/{}/{}s/{}".format(mano_host, mano_port, tenant, datacenter, args.item, args.name)
        mano_response = requests.delete(URLrequest)
        logger.debug("openmano response: %s", mano_response.text )
        result = 0 if mano_response.status_code==200 else mano_response.status_code
        content = mano_response.json()
        # print(json.dumps(content, indent=4))
        if mano_response.status_code == 200:
            print(content['result'])
        else:
            print(content['error']['description'])
        return result
    elif args.action=="create":
        headers_req = {'content-type': 'application/yaml'}
        if args.file:
            create_dict = _load_file_or_yaml(args.file)
            if args.item not in create_dict:
                create_dict = {args.item: create_dict}
        else:
            create_dict = {args.item:{}}
        if args.name:
            create_dict[args.item]['name'] = args.name
        #if args.description:
        #    create_dict[args.item]['description'] = args.description
        if args.item=="network":
            if args.bind_net:
                create_dict[args.item]['bind_net'] = args.bind_net
            if args.type:
                create_dict[args.item]['type'] = args.type
            if args.shared:
                create_dict[args.item]['shared'] = args.shared
        if "name" not in create_dict[args.item]:
            print("You must provide a name in the descriptor file or with the --name option")
            return
        payload_req = yaml.safe_dump(create_dict, explicit_start=True, indent=4, default_flow_style=False, tags=False,
                                     allow_unicode=True)
        logger.debug("openmano request: %s", payload_req)
        URLrequest = "http://{}:{}/openmano/{}/vim/{}/{}s".format(mano_host, mano_port, tenant, datacenter, args.item)
        mano_response = requests.post(URLrequest, headers = headers_req, data=payload_req)
        logger.debug("openmano response: %s", mano_response.text )
        if args.verbose==None:
            args.verbose=0
        return _print_verbose(mano_response, args.verbose)


def _get_items(item, item_name_id=None, datacenter=None, tenant=None):
    URLrequest = "http://{}:{}/openmano".format(mano_host, mano_port)
    if tenant:
        URLrequest += "/" + tenant
    if datacenter:
        URLrequest += "/vim/" + datacenter
    if item:
        URLrequest += "/" + item +"s"
    if item_name_id:
        URLrequest += "/" + item_name_id
    mano_response = requests.get(URLrequest)
    logger.debug("openmano response: %s", mano_response.text )

    return mano_response


def vim_net_sdn_attach(args):
    #Verify the network exists in the vim
    tenant = _get_tenant()
    datacenter = _get_datacenter(args.datacenter, tenant)
    result = _get_items('network', item_name_id=args.vim_net, datacenter=datacenter, tenant=tenant)
    content = yaml.load(result.content)
    if 'networks' in content:
        raise OpenmanoCLIError('More than one network in the vim named ' + args.vim_net + '. Use uuid instead')
    if 'error' in content:
        raise OpenmanoCLIError(yaml.safe_dump(content))
    network_uuid = content['network']['id']

    #Make call to attach the dataplane port to the SND network associated to the vim network
    headers_req = {'content-type': 'application/yaml'}
    payload_req = {'port': args.port}
    if args.vlan:
        payload_req['vlan'] = int(args.vlan)
    if args.mac:
        payload_req['mac'] = args.mac

    URLrequest = "http://{}:{}/openmano/{}/vim/{}/network/{}/attach".format(mano_host, mano_port, tenant, datacenter, network_uuid)
    logger.debug("openmano request: %s", payload_req)
    mano_response = requests.post(URLrequest, headers=headers_req, data=json.dumps(payload_req))
    logger.debug("openmano response: %s", mano_response.text)
    result = _print_verbose(mano_response, args.verbose)
    return result


def vim_net_sdn_detach(args):
    if not args.all and not args.id:
        print("--all or --id must be used")
        return 1

    # Verify the network exists in the vim
    tenant = _get_tenant()
    datacenter = _get_datacenter(args.datacenter, tenant)
    result = _get_items('network', item_name_id=args.vim_net, datacenter=datacenter, tenant=tenant)
    content = yaml.load(result.content)
    if 'networks' in content:
        raise OpenmanoCLIError('More than one network in the vim named ' + args.vim_net + '. Use uuid instead')
    if 'error' in content:
        raise OpenmanoCLIError(yaml.safe_dump(content))
    network_uuid = content['network']['id']

    if not args.force:
        r = input("Confirm action' (y/N)? ")
        if len(r) == 0 or r[0].lower() != "y":
            return 0

    if args.id:
        URLrequest = "http://{}:{}/openmano/{}/vim/{}/network/{}/detach/{}".format(
            mano_host, mano_port, tenant, datacenter, network_uuid, args.id)
    else:
        URLrequest = "http://{}:{}/openmano/{}/vim/{}/network/{}/detach".format(
            mano_host, mano_port, tenant, datacenter, network_uuid)
    mano_response = requests.delete(URLrequest)
    logger.debug("openmano response: %s", mano_response.text)
    result = _print_verbose(mano_response, args.verbose)
    return result


def datacenter_net_action(args):
    if args.action == "net-update":
        print("This command is deprecated, use 'openmano datacenter-netmap-delete --all' and 'openmano"
              " datacenter-netmap-import' instead!!!")
        print()
        args.action = "netmap-delete"
        args.netmap = None
        args.all = True
        r = datacenter_netmap_action(args)
        if r == 0:
            args.force = True
            args.action = "netmap-import"
            r = datacenter_netmap_action(args)
        return r

    if args.action == "net-edit":
        args.netmap = args.net
        args.name = None
    elif args.action == "net-list":
        args.netmap = None
    elif args.action == "net-delete":
        args.netmap = args.net
        args.all = False

    args.action = "netmap" + args.action[3:]
    args.vim_name=None
    args.vim_id=None
    print("This command is deprecated, use 'openmano datacenter-{}' instead!!!".format(args.action))
    print()
    return datacenter_netmap_action(args)

def datacenter_netmap_action(args):
    tenant = _get_tenant()
    datacenter = _get_datacenter(args.datacenter, tenant)
    # print("datacenter_netmap_action",args)
    payload_req = None
    if args.verbose==None:
        args.verbose=0
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}
    URLrequest = "http://{}:{}/openmano/{}/datacenters/{}/netmaps".format(mano_host, mano_port, tenant, datacenter)

    if args.action=="netmap-list":
        if args.netmap:
            URLrequest += "/" + args.netmap
            args.verbose += 1
        mano_response = requests.get(URLrequest)

    elif args.action=="netmap-delete":
        if args.netmap and args.all:
            print("you can not use a netmap name and the option --all at the same time")
            return 1
        if args.netmap:
            force_text= "Delete default netmap '{}' from datacenter '{}' (y/N)? ".format(args.netmap, datacenter)
            URLrequest += "/" + args.netmap
        elif args.all:
            force_text="Delete all default netmaps from datacenter '{}' (y/N)? ".format(datacenter)
        else:
            print("you must specify a netmap name or the option --all")
            return 1
        if not args.force:
            r = input(force_text)
            if  len(r)>0  and r[0].lower()=="y":
                pass
            else:
                return 0
        mano_response = requests.delete(URLrequest, headers=headers_req)
    elif args.action=="netmap-import":
        if not args.force:
            r = input("Create all the available networks from datacenter '{}' as default netmaps (y/N)? ".format(datacenter))
            if  len(r)>0  and r[0].lower()=="y":
                pass
            else:
                return 0
        URLrequest += "/upload"
        mano_response = requests.post(URLrequest, headers=headers_req)
    elif args.action=="netmap-edit" or args.action=="netmap-create":
        if args.file:
            payload = _load_file_or_yaml(args.file)
        else:
            payload = {}
        if "netmap" not in payload:
            payload = {"netmap": payload}
        if args.name:
            payload["netmap"]["name"] = args.name
        if args.vim_id:
            payload["netmap"]["vim_id"] = args.vim_id
        if args.action=="netmap-create" and args.vim_name:
            payload["netmap"]["vim_name"] = args.vim_name
        payload_req = json.dumps(payload)
        logger.debug("openmano request: %s", payload_req)

        if args.action=="netmap-edit" and not args.force:
            if len(payload["netmap"]) == 0:
                print("You must supply some parameter to edit")
                return 1
            r = input("Edit default netmap '{}' from datacenter '{}' (y/N)? ".format(args.netmap, datacenter))
            if  len(r)>0  and r[0].lower()=="y":
                pass
            else:
                return 0
            URLrequest += "/" + args.netmap
            mano_response = requests.put(URLrequest, headers=headers_req, data=payload_req)
        else: #netmap-create
            if "vim_name" not in payload["netmap"] and "vim_id" not in payload["netmap"]:
                print("You must supply either --vim-id or --vim-name option; or include one of them in the file"
                      " descriptor")
                return 1
            mano_response = requests.post(URLrequest, headers=headers_req, data=payload_req)

    logger.debug("openmano response: %s", mano_response.text )
    return _print_verbose(mano_response, args.verbose)


def element_edit(args):
    element = _get_item_uuid(args.element, args.name)
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}
    URLrequest = "http://{}:{}/openmano/{}/{}".format(mano_host, mano_port, args.element, element)
    payload=_load_file_or_yaml(args.file)
    if args.element[:-1] not in payload:
        payload = {args.element[:-1]: payload }
    payload_req = json.dumps(payload)

    # print(payload_req)
    if not args.force or (args.name==None and args.filer==None):
        r = input(" Edit " + args.element[:-1] + " " + args.name + " (y/N)? ")
        if  len(r)>0  and r[0].lower()=="y":
            pass
        else:
            return 0
    logger.debug("openmano request: %s", payload_req)
    mano_response = requests.put(URLrequest, headers=headers_req, data=payload_req)
    logger.debug("openmano response: %s", mano_response.text )
    if args.verbose==None:
        args.verbose=0
    if args.name!=None:
        args.verbose += 1
    return _print_verbose(mano_response, args.verbose)


def datacenter_edit(args):
    tenant = _get_tenant()
    element = _get_item_uuid('datacenters', args.name, tenant)
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}
    URLrequest = "http://{}:{}/openmano/datacenters/{}".format(mano_host, mano_port, element)

    has_arguments = False
    if args.file != None:
        has_arguments = True
        payload = _load_file_or_yaml(args.file)
    else:
        payload = {}

    if args.sdn_controller != None:
        has_arguments = True
        if not 'config' in payload:
            payload['config'] = {}
        if not 'sdn-controller' in payload['config']:
            payload['config']['sdn-controller'] = {}
        if args.sdn_controller == 'null':
            payload['config']['sdn-controller'] = None
        else:
            payload['config']['sdn-controller'] = _get_item_uuid("sdn_controllers", args.sdn_controller, tenant)

    if not has_arguments:
        raise OpenmanoCLIError("At least one argument must be provided to modify the datacenter")

    if 'datacenter' not in payload:
        payload = {'datacenter': payload}
    payload_req = json.dumps(payload)

    # print(payload_req)
    if not args.force or (args.name == None and args.filer == None):
        r = input(" Edit datacenter " + args.name + " (y/N)? ")
        if len(r) > 0 and r[0].lower() == "y":
            pass
        else:
            return 0
    logger.debug("openmano request: %s", payload_req)
    mano_response = requests.put(URLrequest, headers=headers_req, data=payload_req)
    logger.debug("openmano response: %s", mano_response.text)
    if args.verbose == None:
        args.verbose = 0
    if args.name != None:
        args.verbose += 1
    return _print_verbose(mano_response, args.verbose)


# WIM
def wim_account_create(args):
    tenant = _get_tenant()
    wim = _get_wim(args.name)
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}

    wim_dict = {}
    if args.account_name is not None:
        wim_dict['name'] = args.account_name
    if args.user is not None:
        wim_dict['user'] = args.user
    if args.password is not None:
        wim_dict['password'] = args.password
    if args.config is not None:
        wim_dict["config"] = _load_file_or_yaml(args.config)

    payload_req = json.dumps({"wim_account": wim_dict})

    URLrequest = "http://{}:{}/openmano/{}/wims/{}".format(mano_host, mano_port, tenant, wim)
    logger.debug("openmano request: %s", payload_req)
    mano_response = requests.post(URLrequest, headers=headers_req, data=payload_req)
    logger.debug("openmano response: %s", mano_response.text)
    result = _print_verbose(mano_response, args.verbose)
    # provide addional information if error
    if mano_response.status_code != 200:
        content = mano_response.json()
        if "already in use for  'name'" in content['error']['description'] and \
                "to database wim_tenants table" in content['error']['description']:
            print("Try to specify a different name with --wim-tenant-name")
    return result


def wim_account_delete(args):
    if args.all:
        tenant = "any"
    else:
        tenant = _get_tenant()
    wim = _get_wim(args.name, tenant)
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}
    URLrequest = "http://{}:{}/openmano/{}/wims/{}".format(mano_host, mano_port, tenant, wim)
    mano_response = requests.delete(URLrequest, headers=headers_req)
    logger.debug("openmano response: %s", mano_response.text)
    content = mano_response.json()
    # print(json.dumps(content, indent=4))
    result = 0 if mano_response.status_code == 200 else mano_response.status_code
    if mano_response.status_code == 200:
        print(content['result'])
    else:
        print(content['error']['description'])
    return result


def wim_account_edit(args):
    tenant = _get_tenant()
    wim = _get_wim(args.name)
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}

    wim_dict = {}
    if not args.account_name:
        wim_dict['name'] = args.vim_tenant_name
    if not args.user:
        wim_dict['user'] = args.user
    if not args.password:
        wim_dict['password'] = args.password
    if not args.config:
        wim_dict["config"] = _load_file_or_yaml(args.config)

    payload_req = json.dumps({"wim_account": wim_dict})

    # print(payload_req)

    URLrequest = "http://{}:{}/openmano/{}/wims/{}".format(mano_host, mano_port, tenant, wim)
    logger.debug("openmano request: %s", payload_req)
    mano_response = requests.post(URLrequest, headers=headers_req, data=payload_req)
    logger.debug("openmano response: %s", mano_response.text)
    result = _print_verbose(mano_response, args.verbose)
    # provide addional information if error
    if mano_response.status_code != 200:
        content = mano_response.json()
        if "already in use for  'name'" in content['error']['description'] and \
                "to database wim_tenants table" in content['error']['description']:
            print("Try to specify a different name with --wim-tenant-name")
    return result

def wim_create(args):
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}
    wim_dict = {"name": args.name, "wim_url": args.url}
    if args.description != None:
        wim_dict["description"] = args.description
    if args.type != None:
        wim_dict["type"] = args.type
    if args.config != None:
        wim_dict["config"] = _load_file_or_yaml(args.config)

    payload_req = json.dumps({"wim": wim_dict})

    URLrequest = "http://{}:{}/openmano/wims".format(mano_host, mano_port)
    logger.debug("openmano request: %s", payload_req)
    mano_response = requests.post(URLrequest, headers=headers_req, data=payload_req)
    logger.debug("openmano response: %s", mano_response.text)
    return _print_verbose(mano_response, args.verbose)


def wim_edit(args):
    tenant = _get_tenant()
    element = _get_item_uuid('wims', args.name, tenant)
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}
    URLrequest = "http://{}:{}/openmano/wims/{}".format(mano_host, mano_port, element)

    has_arguments = False
    if args.file != None:
        has_arguments = True
        payload = _load_file_or_yaml(args.file)
    else:
        payload = {}

    if not has_arguments:
        raise OpenmanoCLIError("At least one argument must be provided to modify the wim")

    if 'wim' not in payload:
        payload = {'wim': payload}
    payload_req = json.dumps(payload)

    # print(payload_req)
    if not args.force or (args.name == None and args.filer == None):
        r = input(" Edit wim " + args.name + " (y/N)? ")
        if len(r) > 0 and r[0].lower() == "y":
            pass
        else:
            return 0
    logger.debug("openmano request: %s", payload_req)
    mano_response = requests.put(URLrequest, headers=headers_req, data=payload_req)
    logger.debug("openmano response: %s", mano_response.text)
    if args.verbose == None:
        args.verbose = 0
    if args.name != None:
        args.verbose += 1
    return _print_verbose(mano_response, args.verbose)


def wim_delete(args):
    # print("wim-delete",args)
    todelete = _get_item_uuid("wims", args.name, "any")
    if not args.force:
        r = input("Delete wim {} (y/N)? ".format(args.name))
        if not (len(r) > 0 and r[0].lower() == "y"):
            return 0
    URLrequest = "http://{}:{}/openmano/wims/{}".format(mano_host, mano_port, todelete)
    mano_response = requests.delete(URLrequest)
    logger.debug("openmano response: %s", mano_response.text)
    result = 0 if mano_response.status_code == 200 else mano_response.status_code
    content = mano_response.json()
    # print(json.dumps(content, indent=4)
    if mano_response.status_code == 200:
        print(content['result'])
    else:
        print(content['error']['description'])
    return result


def wim_list(args):
    # print("wim-list",args)
    tenant = 'any' if args.all else _get_tenant()

    if args.name:
        toshow = _get_item_uuid("wims", args.name, tenant)
        URLrequest = "http://{}:{}/openmano/{}/wims/{}".format(mano_host, mano_port, tenant, toshow)
    else:
        URLrequest = "http://{}:{}/openmano/{}/wims".format(mano_host, mano_port, tenant)
    mano_response = requests.get(URLrequest)
    logger.debug("openmano response: %s", mano_response.text)
    if args.verbose == None:
        args.verbose = 0
    if args.name != None:
        args.verbose += 1
    return _print_verbose(mano_response, args.verbose)


def wim_port_mapping_set(args):
    tenant = _get_tenant()
    wim = _get_wim(args.name, tenant)
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}

    if not args.file:
        raise OpenmanoCLIError(
            "No yaml/json has been provided specifying the WIM port mapping")
    wim_port_mapping = _load_file_or_yaml(args.file)

    payload_req = json.dumps({"wim_port_mapping": wim_port_mapping})

    # read
    URLrequest = "http://{}:{}/openmano/{}/wims/{}/port_mapping".format(mano_host, mano_port, tenant, wim)
    mano_response = requests.get(URLrequest)
    logger.debug("openmano response: %s", mano_response.text)
    port_mapping = mano_response.json()

    if mano_response.status_code != 200:
        str(mano_response.json())
        raise OpenmanoCLIError("openmano client error: {}".format(port_mapping['error']['description']))
    # TODO: check this if statement
    if len(port_mapping["wim_port_mapping"]) > 0:
        if not args.force:
            r = input("WIM {} already contains a port mapping. Overwrite? (y/N)? ".format(wim))
            if not (len(r) > 0 and r[0].lower() == "y"):
                return 0

        # clear
        URLrequest = "http://{}:{}/openmano/{}/wims/{}/port_mapping".format(mano_host, mano_port, tenant, wim)
        mano_response = requests.delete(URLrequest)
        logger.debug("openmano response: %s", mano_response.text)
        if mano_response.status_code != 200:
            return _print_verbose(mano_response, args.verbose)

    # set
    URLrequest = "http://{}:{}/openmano/{}/wims/{}/port_mapping".format(mano_host, mano_port, tenant, wim)
    logger.debug("openmano request: %s", payload_req)
    mano_response = requests.post(URLrequest, headers=headers_req, data=payload_req)
    logger.debug("openmano response: %s", mano_response.text)
    return _print_verbose(mano_response, 4)


def wim_port_mapping_list(args):
    tenant = _get_tenant()
    wim = _get_wim(args.name, tenant)

    URLrequest = "http://{}:{}/openmano/{}/wims/{}/port_mapping".format(mano_host, mano_port, tenant, wim)
    mano_response = requests.get(URLrequest)
    logger.debug("openmano response: %s", mano_response.text)

    return _print_verbose(mano_response, 4)


def wim_port_mapping_clear(args):
    tenant = _get_tenant()
    wim = _get_wim(args.name, tenant)

    if not args.force:
        r = input("Clear WIM port mapping for wim {} (y/N)? ".format(wim))
        if not (len(r) > 0 and r[0].lower() == "y"):
            return 0

    URLrequest = "http://{}:{}/openmano/{}/wims/{}/port_mapping".format(mano_host, mano_port, tenant, wim)
    mano_response = requests.delete(URLrequest)
    logger.debug("openmano response: %s", mano_response.text)
    content = mano_response.json()
    # print(json.dumps(content, indent=4))
    result = 0 if mano_response.status_code == 200 else mano_response.status_code
    if mano_response.status_code == 200:
        print(content['result'])
    else:
        print(content['error']['description'])
    return result


def version(args):
    headers_req = {'Accept': 'application/json', 'content-type': 'application/json'}
    URLrequest = "http://{}:{}/openmano/version".format(mano_host, mano_port)

    mano_response = requests.get(URLrequest, headers=headers_req)
    logger.debug("openmano response: %s", mano_response.text)
    print(mano_response.text)


def main():
    global mano_host
    global mano_port
    global mano_tenant
    global logger
    mano_tenant = os.getenv('OPENMANO_TENANT', None)
    mano_host = os.getenv('OPENMANO_HOST',"localhost")
    mano_port = os.getenv('OPENMANO_PORT',"9090")
    mano_datacenter = os.getenv('OPENMANO_DATACENTER',None)
    # WIM env variable for default WIM
    mano_wim = os.getenv('OPENMANO_WIM', None)

    main_parser = ThrowingArgumentParser(description='User program to interact with OPENMANO-SERVER (openmanod)')
    main_parser.add_argument('--version', action='version', help="get version of this client",
                            version='%(prog)s client version ' + __version__ +
                                    " (Note: use '%(prog)s version' to get server version)")

    subparsers = main_parser.add_subparsers(help='commands')

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('--verbose', '-v', action='count', help="increase verbosity level. Use several times")
    parent_parser.add_argument('--debug', '-d', action='store_true', help="show debug information")

    config_parser = subparsers.add_parser('config', parents=[parent_parser], help="prints configuration values")
    config_parser.add_argument("-n", action="store_true", help="resolves tenant and datacenter names")
    config_parser.set_defaults(func=config)

    version_parser = subparsers.add_parser('version', parents=[parent_parser], help="get server version")
    version_parser.set_defaults(func=version)

    vnf_create_parser = subparsers.add_parser('vnf-create', parents=[parent_parser], help="adds a vnf into the catalogue")
    vnf_create_parser.add_argument("file", action="store", help="location of the JSON file describing the VNF").completer = FilesCompleter
    vnf_create_parser.add_argument("--name", action="store", help="name of the VNF (if it exists in the VNF descriptor, it is overwritten)")
    vnf_create_parser.add_argument("--description", action="store", help="description of the VNF (if it exists in the VNF descriptor, it is overwritten)")
    vnf_create_parser.add_argument("--image-path", action="store",  help="change image path locations (overwritten)")
    vnf_create_parser.add_argument("--image-name", action="store",  help="change image name (overwritten)")
    vnf_create_parser.add_argument("--image-checksum", action="store",  help="change image checksum (overwritten)")
    vnf_create_parser.set_defaults(func=vnf_create)

    vnf_list_parser = subparsers.add_parser('vnf-list', parents=[parent_parser], help="lists information about a vnf")
    vnf_list_parser.add_argument("name", nargs='?', help="name of the VNF")
    vnf_list_parser.add_argument("-a", "--all", action="store_true", help="shows all vnfs, not only the owned or public ones")
    #vnf_list_parser.add_argument('--descriptor', help="prints the VNF descriptor", action="store_true")
    vnf_list_parser.set_defaults(func=vnf_list)

    vnf_delete_parser = subparsers.add_parser('vnf-delete', parents=[parent_parser], help="deletes a vnf from the catalogue")
    vnf_delete_parser.add_argument("name", action="store", help="name or uuid of the VNF to be deleted")
    vnf_delete_parser.add_argument("-f", "--force", action="store_true", help="forces deletion without asking")
    vnf_delete_parser.add_argument("-a", "--all", action="store_true", help="allow delete not owned or privated one")
    vnf_delete_parser.set_defaults(func=vnf_delete)

    scenario_create_parser = subparsers.add_parser('scenario-create', parents=[parent_parser], help="adds a scenario into the OPENMANO DB")
    scenario_create_parser.add_argument("file", action="store", help="location of the YAML file describing the scenario").completer = FilesCompleter
    scenario_create_parser.add_argument("--name", action="store", help="name of the scenario (if it exists in the YAML scenario, it is overwritten)")
    scenario_create_parser.add_argument("--description", action="store", help="description of the scenario (if it exists in the YAML scenario, it is overwritten)")
    scenario_create_parser.set_defaults(func=scenario_create)

    scenario_list_parser = subparsers.add_parser('scenario-list', parents=[parent_parser], help="lists information about a scenario")
    scenario_list_parser.add_argument("name", nargs='?', help="name of the scenario")
    #scenario_list_parser.add_argument('--descriptor', help="prints the scenario descriptor", action="store_true")
    scenario_list_parser.add_argument("-a", "--all", action="store_true", help="shows all scenarios, not only the owned or public ones")
    scenario_list_parser.set_defaults(func=scenario_list)

    scenario_delete_parser = subparsers.add_parser('scenario-delete', parents=[parent_parser], help="deletes a scenario from the OPENMANO DB")
    scenario_delete_parser.add_argument("name", action="store", help="name or uuid of the scenario to be deleted")
    scenario_delete_parser.add_argument("-f", "--force", action="store_true", help="forces deletion without asking")
    scenario_delete_parser.add_argument("-a", "--all", action="store_true", help="allow delete not owned or privated one")
    scenario_delete_parser.set_defaults(func=scenario_delete)

    scenario_deploy_parser = subparsers.add_parser('scenario-deploy', parents=[parent_parser], help="deploys a scenario")
    scenario_deploy_parser.add_argument("scenario", action="store", help="name or uuid of the scenario to be deployed")
    scenario_deploy_parser.add_argument("name", action="store", help="name of the instance")
    scenario_deploy_parser.add_argument("--nostart", action="store_true", help="does not start the vms, just reserve resources")
    scenario_deploy_parser.add_argument("--datacenter", action="store", help="specifies the datacenter. Needed if several datacenters are available")
    scenario_deploy_parser.add_argument("--description", action="store", help="description of the instance")
    scenario_deploy_parser.set_defaults(func=scenario_deploy)

    scenario_deploy_parser = subparsers.add_parser('scenario-verify', help="verifies if a scenario can be deployed (deploys it and deletes it)")
    scenario_deploy_parser.add_argument("scenario", action="store", help="name or uuid of the scenario to be verified")
    scenario_deploy_parser.add_argument('--debug', '-d', action='store_true', help="show debug information")
    scenario_deploy_parser.set_defaults(func=scenario_verify)

    instance_scenario_create_parser = subparsers.add_parser('instance-scenario-create', parents=[parent_parser], help="deploys a scenario")
    instance_scenario_create_parser.add_argument("file", nargs='?', help="descriptor of the instance. Must be a file or yaml/json text")
    instance_scenario_create_parser.add_argument("--scenario", action="store", help="name or uuid of the scenario to be deployed")
    instance_scenario_create_parser.add_argument("--name", action="store", help="name of the instance")
    instance_scenario_create_parser.add_argument("--nostart", action="store_true", help="does not start the vms, just reserve resources")
    instance_scenario_create_parser.add_argument("--datacenter", action="store", help="specifies the datacenter. Needed if several datacenters are available")
    instance_scenario_create_parser.add_argument("--netmap-use", action="append", type=str, dest="netmap_use", help="indicates a datacenter network to map a scenario network 'scenario-network=datacenter-network'. Can be used several times")
    instance_scenario_create_parser.add_argument("--netmap-create", action="append", type=str, dest="netmap_create", help="the scenario network must be created at datacenter 'scenario-network[=datacenter-network-name]' . Can be used several times")
    instance_scenario_create_parser.add_argument("--keypair", action="append", type=str, dest="keypair", help="public key for ssh access. Format '[user:]key1[,key2...]'. Can be used several times")
    instance_scenario_create_parser.add_argument("--keypair-auto", action="store_true", dest="keypair_auto", help="Inject the user ssh-keys found at $HOME/.ssh directory")
    instance_scenario_create_parser.add_argument("--description", action="store", help="description of the instance")
    instance_scenario_create_parser.set_defaults(func=instance_create)

    instance_scenario_list_parser = subparsers.add_parser('instance-scenario-list', parents=[parent_parser], help="lists information about a scenario instance")
    instance_scenario_list_parser.add_argument("name", nargs='?', help="name of the scenario instance")
    instance_scenario_list_parser.add_argument("-a", "--all", action="store_true", help="shows all instance-scenarios, not only the owned")
    instance_scenario_list_parser.set_defaults(func=instance_scenario_list)

    instance_scenario_delete_parser = subparsers.add_parser('instance-scenario-delete', parents=[parent_parser], help="deletes a scenario instance (and deletes all VM and net instances in VIM)")
    instance_scenario_delete_parser.add_argument("name", action="store", help="name or uuid of the scenario instance to be deleted")
    instance_scenario_delete_parser.add_argument("-f", "--force", action="store_true", help="forces deletion without asking")
    instance_scenario_delete_parser.add_argument("-a", "--all", action="store_true", help="allow delete not owned or privated one")
    instance_scenario_delete_parser.set_defaults(func=instance_scenario_delete)

    instance_scenario_action_parser = subparsers.add_parser('instance-scenario-action', parents=[parent_parser], help="invoke an action over part or the whole scenario instance")
    instance_scenario_action_parser.add_argument("name", action="store", help="name or uuid of the scenario instance")
    instance_scenario_action_parser.add_argument("action", action="store", type=str, \
            choices=["start","pause","resume","shutoff","shutdown","forceOff","rebuild","reboot", "console", "add_public_key","vdu-scaling"],\
            help="action to send")
    instance_scenario_action_parser.add_argument("param", nargs='?', help="addional param of the action. e.g. console: novnc; reboot: type; vdu-scaling: '[{vdu-id: xxx, type: create|delete, count: 1}]'")
    instance_scenario_action_parser.add_argument("--vnf", action="append", help="VNF to act on (can use several entries)")
    instance_scenario_action_parser.add_argument("--vm", action="append", help="VM to act on (can use several entries)")
    instance_scenario_action_parser.set_defaults(func=instance_scenario_action)

    action_parser = subparsers.add_parser('action-list', parents=[parent_parser], help="get action over an instance status")
    action_parser.add_argument("id", nargs='?', action="store", help="action id")
    action_parser.add_argument("--instance", action="store", help="fitler by this instance_id")
    action_parser.add_argument("--all", action="store", help="Not filter by tenant")
    action_parser.set_defaults(func=get_action)

    #instance_scenario_status_parser = subparsers.add_parser('instance-scenario-status', help="show the status of a scenario instance")
    #instance_scenario_status_parser.add_argument("name", action="store", help="name or uuid of the scenario instance")
    #instance_scenario_status_parser.set_defaults(func=instance_scenario_status)

    tenant_create_parser = subparsers.add_parser('tenant-create', parents=[parent_parser], help="creates a new tenant")
    tenant_create_parser.add_argument("name", action="store", help="name for the tenant")
    tenant_create_parser.add_argument("--description", action="store", help="description of the tenant")
    tenant_create_parser.set_defaults(func=tenant_create)

    tenant_delete_parser = subparsers.add_parser('tenant-delete', parents=[parent_parser], help="deletes a tenant from the catalogue")
    tenant_delete_parser.add_argument("name", action="store", help="name or uuid of the tenant to be deleted")
    tenant_delete_parser.add_argument("-f", "--force", action="store_true", help="forces deletion without asking")
    tenant_delete_parser.set_defaults(func=tenant_delete)

    tenant_list_parser = subparsers.add_parser('tenant-list', parents=[parent_parser], help="lists information about a tenant")
    tenant_list_parser.add_argument("name", nargs='?', help="name or uuid of the tenant")
    tenant_list_parser.set_defaults(func=tenant_list)

    element_edit_parser = subparsers.add_parser('tenant-edit', parents=[parent_parser], help="edits one tenant")
    element_edit_parser.add_argument("name", help="name or uuid of the tenant")
    element_edit_parser.add_argument("file", help="json/yaml text or file with the changes").completer = FilesCompleter
    element_edit_parser.add_argument("-f","--force", action="store_true", help="do not prompt for confirmation")
    element_edit_parser.set_defaults(func=element_edit, element='tenants')

    datacenter_create_parser = subparsers.add_parser('datacenter-create', parents=[parent_parser], help="creates a new datacenter")
    datacenter_create_parser.add_argument("name", action="store", help="name for the datacenter")
    datacenter_create_parser.add_argument("url", action="store", help="url for the datacenter")
    datacenter_create_parser.add_argument("--url_admin", action="store", help="url for administration for the datacenter")
    datacenter_create_parser.add_argument("--type", action="store", help="datacenter type: openstack or openvim (default)")
    datacenter_create_parser.add_argument("--config", action="store", help="aditional configuration in json/yaml format")
    datacenter_create_parser.add_argument("--description", action="store", help="description of the datacenter")
    datacenter_create_parser.add_argument("--sdn-controller", action="store", help="Name or uuid of the SDN controller to be used", dest='sdn_controller')
    datacenter_create_parser.set_defaults(func=datacenter_create)

    datacenter_delete_parser = subparsers.add_parser('datacenter-delete', parents=[parent_parser], help="deletes a datacenter from the catalogue")
    datacenter_delete_parser.add_argument("name", action="store", help="name or uuid of the datacenter to be deleted")
    datacenter_delete_parser.add_argument("-f", "--force", action="store_true", help="forces deletion without asking")
    datacenter_delete_parser.set_defaults(func=datacenter_delete)

    datacenter_edit_parser = subparsers.add_parser('datacenter-edit', parents=[parent_parser], help="Edit datacenter")
    datacenter_edit_parser.add_argument("name", help="name or uuid of the datacenter")
    datacenter_edit_parser.add_argument("--file", help="json/yaml text or file with the changes").completer = FilesCompleter
    datacenter_edit_parser.add_argument("--sdn-controller", action="store",
                                          help="Name or uuid of the SDN controller to be used. Specify 'null' to clear entry", dest='sdn_controller')
    datacenter_edit_parser.add_argument("-f", "--force", action="store_true", help="do not prompt for confirmation")
    datacenter_edit_parser.set_defaults(func=datacenter_edit)

    datacenter_list_parser = subparsers.add_parser('datacenter-list', parents=[parent_parser], help="lists information about a datacenter")
    datacenter_list_parser.add_argument("name", nargs='?', help="name or uuid of the datacenter")
    datacenter_list_parser.add_argument("-a", "--all", action="store_true", help="shows all datacenters, not only datacenters attached to tenant")
    datacenter_list_parser.set_defaults(func=datacenter_list)

    datacenter_attach_parser = subparsers.add_parser('datacenter-attach', parents=[parent_parser], help="associates a datacenter to the operating tenant")
    datacenter_attach_parser.add_argument("name", help="name or uuid of the datacenter")
    datacenter_attach_parser.add_argument('--vim-tenant-id', action='store', help="specify a datacenter tenant to use. A new one is created by default")
    datacenter_attach_parser.add_argument('--vim-tenant-name', action='store', help="specify a datacenter tenant name.")
    datacenter_attach_parser.add_argument("--user", action="store", help="user credentials for the datacenter")
    datacenter_attach_parser.add_argument("--password", action="store", help="password credentials for the datacenter")
    datacenter_attach_parser.add_argument("--config", action="store", help="aditional configuration in json/yaml format")
    datacenter_attach_parser.set_defaults(func=datacenter_attach)

    datacenter_edit_vim_tenant_parser = subparsers.add_parser('datacenter-edit-vim-tenant', parents=[parent_parser],
                                                     help="Edit the association of a datacenter to the operating tenant")
    datacenter_edit_vim_tenant_parser.add_argument("name", help="name or uuid of the datacenter")
    datacenter_edit_vim_tenant_parser.add_argument('--vim-tenant-id', action='store',
                                          help="specify a datacenter tenant to use. A new one is created by default")
    datacenter_edit_vim_tenant_parser.add_argument('--vim-tenant-name', action='store', help="specify a datacenter tenant name.")
    datacenter_edit_vim_tenant_parser.add_argument("--user", action="store", help="user credentials for the datacenter")
    datacenter_edit_vim_tenant_parser.add_argument("--password", action="store", help="password credentials for the datacenter")
    datacenter_edit_vim_tenant_parser.add_argument("--config", action="store",
                                          help="aditional configuration in json/yaml format")
    datacenter_edit_vim_tenant_parser.set_defaults(func=datacenter_edit_vim_tenant)

    datacenter_detach_parser = subparsers.add_parser('datacenter-detach', parents=[parent_parser], help="removes the association between a datacenter and the operating tenant")
    datacenter_detach_parser.add_argument("name", help="name or uuid of the datacenter")
    datacenter_detach_parser.add_argument("-a", "--all", action="store_true", help="removes all associations from this datacenter")
    datacenter_detach_parser.set_defaults(func=datacenter_detach)

    #=======================datacenter_sdn_port_mapping_xxx section=======================
    #datacenter_sdn_port_mapping_set
    datacenter_sdn_port_mapping_set_parser = subparsers.add_parser('datacenter-sdn-port-mapping-set',
                                                                   parents=[parent_parser],
                                                                   help="Load a file with the mapping of physical ports "
                                                                        "and the ports of the dataplaneswitch controlled "
                                                                        "by a datacenter")
    datacenter_sdn_port_mapping_set_parser.add_argument("name", action="store", help="specifies the datacenter")
    datacenter_sdn_port_mapping_set_parser.add_argument("file",
                                                        help="json/yaml text or file with the port mapping").completer = FilesCompleter
    datacenter_sdn_port_mapping_set_parser.add_argument("-f", "--force", action="store_true",
                                                          help="forces overwriting without asking")
    datacenter_sdn_port_mapping_set_parser.set_defaults(func=datacenter_sdn_port_mapping_set)

    #datacenter_sdn_port_mapping_list
    datacenter_sdn_port_mapping_list_parser = subparsers.add_parser('datacenter-sdn-port-mapping-list',
                                                                    parents=[parent_parser],
                                                                    help="Show the SDN port mapping in a datacenter")
    datacenter_sdn_port_mapping_list_parser.add_argument("name", action="store", help="specifies the datacenter")
    datacenter_sdn_port_mapping_list_parser.set_defaults(func=datacenter_sdn_port_mapping_list)

    # datacenter_sdn_port_mapping_clear
    datacenter_sdn_port_mapping_clear_parser = subparsers.add_parser('datacenter-sdn-port-mapping-clear',
                                                                    parents=[parent_parser],
                                                                    help="Clean the the SDN port mapping in a datacenter")
    datacenter_sdn_port_mapping_clear_parser.add_argument("name", action="store",
                                                         help="specifies the datacenter")
    datacenter_sdn_port_mapping_clear_parser.add_argument("-f", "--force", action="store_true",
                                              help="forces clearing without asking")
    datacenter_sdn_port_mapping_clear_parser.set_defaults(func=datacenter_sdn_port_mapping_clear)
    # =======================

    # =======================sdn_controller_xxx section=======================
    # sdn_controller_create
    sdn_controller_create_parser = subparsers.add_parser('sdn-controller-create', parents=[parent_parser],
                                                        help="Creates an SDN controller entity within RO")
    sdn_controller_create_parser.add_argument("name", help="name of the SDN controller")
    sdn_controller_create_parser.add_argument("--description", action="store", help="description of the SDN controller")
    sdn_controller_create_parser.add_argument("--ip", action="store", help="IP of the SDN controller")
    sdn_controller_create_parser.add_argument("--port", action="store", help="Port of the SDN controller")
    sdn_controller_create_parser.add_argument("--dpid", action="store",
                                             help="DPID of the dataplane switch controlled by this SDN controller")
    sdn_controller_create_parser.add_argument("--type", action="store",
                                             help="Specify the SDN controller type. Valid types are 'opendaylight' and 'floodlight'")
    sdn_controller_create_parser.add_argument("--user", action="store", help="user credentials for the SDN controller")
    sdn_controller_create_parser.add_argument("--passwd", action="store", dest='password',
                                             help="password credentials for the SDN controller")
    sdn_controller_create_parser.set_defaults(func=sdn_controller_create)

    # sdn_controller_edit
    sdn_controller_edit_parser = subparsers.add_parser('sdn-controller-edit', parents=[parent_parser],
                                                        help="Update one or more options of a SDN controller")
    sdn_controller_edit_parser.add_argument("name", help="name or uuid of the SDN controller", )
    sdn_controller_edit_parser.add_argument("--name", action="store", help="Update the name of the SDN controller",
                                              dest='new_name')
    sdn_controller_edit_parser.add_argument("--description", action="store", help="description of the SDN controller")
    sdn_controller_edit_parser.add_argument("--ip", action="store", help="IP of the SDN controller")
    sdn_controller_edit_parser.add_argument("--port", action="store", help="Port of the SDN controller")
    sdn_controller_edit_parser.add_argument("--dpid", action="store",
                                             help="DPID of the dataplane switch controlled by this SDN controller")
    sdn_controller_edit_parser.add_argument("--type", action="store",
                                             help="Specify the SDN controller type. Valid types are 'opendaylight' and 'floodlight'")
    sdn_controller_edit_parser.add_argument("--user", action="store", help="user credentials for the SDN controller")
    sdn_controller_edit_parser.add_argument("--password", action="store",
                                             help="password credentials for the SDN controller", dest='password')
    sdn_controller_edit_parser.add_argument("-f", "--force", action="store_true", help="do not prompt for confirmation")
    #TODO: include option --file
    sdn_controller_edit_parser.set_defaults(func=sdn_controller_edit)

    #sdn_controller_list
    sdn_controller_list_parser = subparsers.add_parser('sdn-controller-list',
                                                                    parents=[parent_parser],
                                                                    help="List the SDN controllers")
    sdn_controller_list_parser.add_argument("name", nargs='?', help="name or uuid of the SDN controller")
    sdn_controller_list_parser.set_defaults(func=sdn_controller_list)

    # sdn_controller_delete
    sdn_controller_delete_parser = subparsers.add_parser('sdn-controller-delete',
                                                                    parents=[parent_parser],
                                                                    help="Delete the the SDN controller")
    sdn_controller_delete_parser.add_argument("name", help="name or uuid of the SDN controller")
    sdn_controller_delete_parser.add_argument("-f", "--force", action="store_true", help="forces deletion without asking")
    sdn_controller_delete_parser.set_defaults(func=sdn_controller_delete)
    # =======================

    # WIM ======================= WIM section==================

    # WIM create
    wim_create_parser = subparsers.add_parser('wim-create',
                                              parents=[parent_parser], help="creates a new wim")
    wim_create_parser.add_argument("name", action="store",
                                   help="name for the wim")
    wim_create_parser.add_argument("url", action="store",
                                   help="url for the wim")
    wim_create_parser.add_argument("--type", action="store",
                                   help="wim type: ietfl2vpn, dynpac, ...")
    wim_create_parser.add_argument("--config", action="store",
                                   help="additional configuration in json/yaml format")
    wim_create_parser.add_argument("--description", action="store",
                                   help="description of the wim")
    wim_create_parser.set_defaults(func=wim_create)

    # WIM delete
    wim_delete_parser = subparsers.add_parser('wim-delete',
                                              parents=[parent_parser], help="deletes a wim from the catalogue")
    wim_delete_parser.add_argument("name", action="store",
                                   help="name or uuid of the wim to be deleted")
    wim_delete_parser.add_argument("-f", "--force", action="store_true",
                                   help="forces deletion without asking")
    wim_delete_parser.set_defaults(func=wim_delete)

    # WIM edit
    wim_edit_parser = subparsers.add_parser('wim-edit',
                                            parents=[parent_parser], help="edits a wim")
    wim_edit_parser.add_argument("name", help="name or uuid of the wim")
    wim_edit_parser.add_argument("--file",
                                 help="json/yaml text or file with the changes")\
                                .completer = FilesCompleter
    wim_edit_parser.add_argument("-f", "--force", action="store_true",
                                 help="do not prompt for confirmation")
    wim_edit_parser.set_defaults(func=wim_edit)

    # WIM list
    wim_list_parser = subparsers.add_parser('wim-list',
                                            parents=[parent_parser],
                                            help="lists information about registered wims")
    wim_list_parser.add_argument("name", nargs='?',
                                 help="name or uuid of the wim")
    wim_list_parser.add_argument("-a", "--all", action="store_true",
                                 help="shows all wims, not only wims attached to tenant")
    wim_list_parser.set_defaults(func=wim_list)

    # WIM account create
    wim_attach_parser = subparsers.add_parser('wim-account-create', parents=
    [parent_parser], help="associates a wim account to the operating tenant")
    wim_attach_parser.add_argument("name", help="name or uuid of the wim")
    wim_attach_parser.add_argument('--account-name', action='store',
                                   help="specify a name for the wim account.")
    wim_attach_parser.add_argument("--user", action="store",
                                   help="user credentials for the wim account")
    wim_attach_parser.add_argument("--password", action="store",
                                   help="password credentials for the wim account")
    wim_attach_parser.add_argument("--config", action="store",
                                   help="additional configuration in json/yaml format")
    wim_attach_parser.set_defaults(func=wim_account_create)

    # WIM account delete
    wim_detach_parser = subparsers.add_parser('wim-account-delete',
                                        parents=[parent_parser],
                                        help="removes the association "
                                                "between a wim account and the operating tenant")
    wim_detach_parser.add_argument("name", help="name or uuid of the wim")
    wim_detach_parser.add_argument("-a", "--all", action="store_true",
                                   help="removes all associations from this wim")
    wim_detach_parser.add_argument("-f", "--force", action="store_true",
                                   help="forces delete without asking")
    wim_detach_parser.set_defaults(func=wim_account_delete)

    # WIM account edit
    wim_attach_edit_parser = subparsers.add_parser('wim-account-edit', parents=
    [parent_parser], help="modifies the association of a wim account to the operating tenant")
    wim_attach_edit_parser.add_argument("name", help="name or uuid of the wim")
    wim_attach_edit_parser.add_argument('--account-name', action='store',
                                   help="specify a name for the wim account.")
    wim_attach_edit_parser.add_argument("--user", action="store",
                                   help="user credentials for the wim account")
    wim_attach_edit_parser.add_argument("--password", action="store",
                                   help="password credentials for the wim account")
    wim_attach_edit_parser.add_argument("--config", action="store",
                                   help="additional configuration in json/yaml format")
    wim_attach_edit_parser.set_defaults(func=wim_account_edit)

    # WIM port mapping set
    wim_port_mapping_set_parser = subparsers.add_parser('wim-port-mapping-set',
                                                        parents=[parent_parser],
                                                        help="Load a file with the mappings "
                                                                "of ports of a WAN switch that is "
                                                                "connected to a PoP and the ports "
                                                                "of the switch controlled by the PoP")
    wim_port_mapping_set_parser.add_argument("name", action="store",
                                             help="specifies the wim")
    wim_port_mapping_set_parser.add_argument("file",
                                             help="json/yaml text or file with the wim port mapping")\
        .completer = FilesCompleter
    wim_port_mapping_set_parser.add_argument("-f", "--force",
                                             action="store_true", help="forces overwriting without asking")
    wim_port_mapping_set_parser.set_defaults(func=wim_port_mapping_set)

    # WIM port mapping list
    wim_port_mapping_list_parser = subparsers.add_parser('wim-port-mapping-list',
            parents=[parent_parser], help="Show the port mappings for a wim")
    wim_port_mapping_list_parser.add_argument("name", action="store",
                                              help="specifies the wim")
    wim_port_mapping_list_parser.set_defaults(func=wim_port_mapping_list)

    # WIM port mapping clear
    wim_port_mapping_clear_parser = subparsers.add_parser('wim-port-mapping-clear',
            parents=[parent_parser], help="Clean the port mapping in a wim")
    wim_port_mapping_clear_parser.add_argument("name", action="store",
                                               help="specifies the wim")
    wim_port_mapping_clear_parser.add_argument("-f", "--force",
                                               action="store_true",
                                               help="forces clearing without asking")
    wim_port_mapping_clear_parser.set_defaults(func=wim_port_mapping_clear)

    # =======================================================

    action_dict={'net-update': 'retrieves external networks from datacenter',
                 'net-edit': 'edits an external network',
                 'net-delete': 'deletes an external network',
                 'net-list': 'lists external networks from a datacenter'
                 }
    for item in action_dict:
        datacenter_action_parser = subparsers.add_parser('datacenter-'+item, parents=[parent_parser], help=action_dict[item])
        datacenter_action_parser.add_argument("datacenter", help="name or uuid of the datacenter")
        if item=='net-edit' or item=='net-delete':
            datacenter_action_parser.add_argument("net", help="name or uuid of the datacenter net")
        if item=='net-edit':
            datacenter_action_parser.add_argument("file", help="json/yaml text or file with the changes").completer = FilesCompleter
        if item!='net-list':
            datacenter_action_parser.add_argument("-f","--force", action="store_true", help="do not prompt for confirmation")
        datacenter_action_parser.set_defaults(func=datacenter_net_action, action=item)


    action_dict={'netmap-import': 'create network senario netmap base on the datacenter networks',
                 'netmap-create': 'create a new network senario netmap',
                 'netmap-edit':   'edit name of a network senario netmap',
                 'netmap-delete': 'deletes a network scenario netmap (--all for clearing all)',
                 'netmap-list':   'list/show network scenario netmaps'
                 }
    for item in action_dict:
        datacenter_action_parser = subparsers.add_parser('datacenter-'+item, parents=[parent_parser], help=action_dict[item])
        datacenter_action_parser.add_argument("--datacenter", help="name or uuid of the datacenter")
        #if item=='net-add':
        #    datacenter_action_parser.add_argument("net", help="name of the network")
        if item=='netmap-delete':
            datacenter_action_parser.add_argument("netmap", nargs='?',help="name or uuid of the datacenter netmap to delete")
            datacenter_action_parser.add_argument("--all", action="store_true", help="delete all netmap of this datacenter")
            datacenter_action_parser.add_argument("-f","--force", action="store_true", help="do not prompt for confirmation")
        if item=='netmap-edit':
            datacenter_action_parser.add_argument("netmap", help="name or uuid of the datacenter netmap do edit")
            datacenter_action_parser.add_argument("file", nargs='?', help="json/yaml text or file with the changes").completer = FilesCompleter
            datacenter_action_parser.add_argument("--name", action='store', help="name to assign to the datacenter netmap")
            datacenter_action_parser.add_argument('--vim-id', action='store', help="specify vim network uuid")
            datacenter_action_parser.add_argument("-f","--force", action="store_true", help="do not prompt for confirmation")
        if item=='netmap-list':
            datacenter_action_parser.add_argument("netmap", nargs='?',help="name or uuid of the datacenter netmap to show")
        if item=='netmap-create':
            datacenter_action_parser.add_argument("file", nargs='?', help="json/yaml text or file descriptor with the changes").completer = FilesCompleter
            datacenter_action_parser.add_argument("--name", action='store', help="name to assign to the datacenter netmap, by default same as vim-name")
            datacenter_action_parser.add_argument('--vim-id', action='store', help="specify vim network uuid")
            datacenter_action_parser.add_argument('--vim-name', action='store', help="specify vim network name")
        if item=='netmap-import':
            datacenter_action_parser.add_argument("-f","--force", action="store_true", help="do not prompt for confirmation")
        datacenter_action_parser.set_defaults(func=datacenter_netmap_action, action=item)

    # =======================vim_net_sdn_xxx section=======================
    # vim_net_sdn_attach
    vim_net_sdn_attach_parser = subparsers.add_parser('vim-net-sdn-attach',
                                                      parents=[parent_parser],
                                                      help="Specify the port to access to an external network using SDN")
    vim_net_sdn_attach_parser.add_argument("vim_net", action="store",
                                                help="Name/id of the network in the vim that will be used to connect to the external network")
    vim_net_sdn_attach_parser.add_argument("port", action="store", help="Specifies the port in the dataplane switch to access to the external network")
    vim_net_sdn_attach_parser.add_argument("--vlan", action="store", help="Specifies the vlan (if any) to use in the defined port")
    vim_net_sdn_attach_parser.add_argument("--mac", action="store", help="Specifies the MAC (if known) of the physical device that will be reachable by this external port")
    vim_net_sdn_attach_parser.add_argument("--datacenter", action="store", help="specifies the datacenter")
    vim_net_sdn_attach_parser.set_defaults(func=vim_net_sdn_attach)

    # vim_net_sdn_detach
    vim_net_sdn_detach_parser = subparsers.add_parser('vim-net-sdn-detach',
                                                           parents=[parent_parser],
                                                           help="Remove the port information to access to an external network using SDN")

    vim_net_sdn_detach_parser.add_argument("vim_net", action="store", help="Name/id of the vim network")
    vim_net_sdn_detach_parser.add_argument("--id", action="store",help="Specify the uuid of the external ports from this network to be detached")
    vim_net_sdn_detach_parser.add_argument("--all", action="store_true", help="Detach all external ports from this network")
    vim_net_sdn_detach_parser.add_argument("-f", "--force", action="store_true", help="forces clearing without asking")
    vim_net_sdn_detach_parser.add_argument("--datacenter", action="store", help="specifies the datacenter")
    vim_net_sdn_detach_parser.set_defaults(func=vim_net_sdn_detach)
    # =======================

    for item in ("network", "tenant", "image"):
        if item=="network":
            command_name = 'vim-net'
        else:
            command_name = 'vim-'+item
        vim_item_list_parser = subparsers.add_parser(command_name + '-list', parents=[parent_parser], help="list the vim " + item + "s")
        vim_item_list_parser.add_argument("name", nargs='?', help="name or uuid of the " + item + "s")
        vim_item_list_parser.add_argument("--datacenter", action="store", help="specifies the datacenter")
        vim_item_list_parser.set_defaults(func=vim_action, item=item, action="list")

        vim_item_del_parser = subparsers.add_parser(command_name + '-delete', parents=[parent_parser], help="list the vim " + item + "s")
        vim_item_del_parser.add_argument("name", help="name or uuid of the " + item + "s")
        vim_item_del_parser.add_argument("--datacenter", action="store", help="specifies the datacenter")
        vim_item_del_parser.set_defaults(func=vim_action, item=item, action="delete")

        if item == "network" or item == "tenant":
            vim_item_create_parser = subparsers.add_parser(command_name + '-create', parents=[parent_parser], help="create a "+item+" at vim")
            vim_item_create_parser.add_argument("file", nargs='?', help="descriptor of the {}. Must be a file or yaml/json text".format(item)).completer = FilesCompleter
            vim_item_create_parser.add_argument("--name", action="store", help="name of the {}".format(item))
            vim_item_create_parser.add_argument("--datacenter", action="store", help="specifies the datacenter")
            if item=="network":
                vim_item_create_parser.add_argument("--type", action="store", help="type of network, data, ptp, bridge")
                vim_item_create_parser.add_argument("--shared", action="store_true", help="Private or shared")
                vim_item_create_parser.add_argument("--bind-net", action="store", help="For openvim datacenter type, net to be bind to, for vlan type, use sufix ':<vlan_tag>'")
            else:
                vim_item_create_parser.add_argument("--description", action="store", help="description of the {}".format(item))
            vim_item_create_parser.set_defaults(func=vim_action, item=item, action="create")

    argcomplete.autocomplete(main_parser)

    try:
        args = main_parser.parse_args()
        #logging info
        level = logging.CRITICAL
        streamformat = "%(asctime)s %(name)s %(levelname)s: %(message)s"
        if "debug" in args and args.debug:
            level = logging.DEBUG
        logging.basicConfig(format=streamformat, level= level)
        logger = logging.getLogger('mano')
        logger.setLevel(level)
        # print("#TODO py3", args)
        result = args.func(args)
        if result == None:
            result = 0
        #for some reason it fails if call exit inside try instance. Need to call exit at the end !?
    except (requests.exceptions.ConnectionError):
        print("Connection error: not possible to contact OPENMANO-SERVER (openmanod)")
        result = -2
    except (KeyboardInterrupt):
        print('Exiting openmano')
        result = -3
    except (SystemExit, ArgumentParserError):
        result = -4
    except (AttributeError):
        print("Type '--help' for more information")
        result = -4
    except OpenmanoCLIError as e:
        # print("#TODO py3", e)
        print(e)
        result = -5

    # print(result)
    exit(result)


if __name__ == '__main__':
    main()

