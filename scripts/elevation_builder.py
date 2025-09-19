import xlsxwriter
import csv
import sys
import os
from os import walk
import argparse
import pprint
import json
import yaml
from argparse import RawTextHelpFormatter


# This is the start of a script that generates elevations

parser = argparse.ArgumentParser(description='''Generates elevations base on a JSON input file.

python3 scripts/elevation_builder.py BareMetal inputs/server_spec.json /Users/zackgrossbart/work/platform-inventory output/elevation.xlsx output/elevation.yaml

''', formatter_class=RawTextHelpFormatter)

parser.add_argument('type', type=str, choices=['NG3', 'NG2', 'BareMetal'], help='The type of rack to build.')
parser.add_argument('serversPath', type=str, help='The path to the server spec.')
parser.add_argument('piPath', type=str, help='The path to the local platform-inventory repo.')
parser.add_argument('outputPath', type=str, help='The path to the elevation to output.')
parser.add_argument('outputYamlPath', type=str, help='The path to the YAML file to output.')

args = parser.parse_args()
outputPath = args.outputPath
outputYamlPath = args.outputYamlPath
serversPath = args.serversPath
piPath = args.piPath
rackType = args.type

# This is the array of colors we will use for server types.
# We use them in order for each class of server in the rack.
COLORS = ['#8EE77F', '#ea686e', '#FCE4D6', '#D9E1F2', '#e67e22', '#f4e0c7']

# This object defines the power phases for the specific rack type.  The power phases must
# match the template phases. Currently all of our racks have three power phases which run
# from the top to the bottom as C, B, and A.  Each phase has the following properties:
#
#   name indicates the name as C, B, or A
#   start indicates the row of the worksheet where the power phase starts
#   end indicates the row of the worksheet where the power phase ends
#   maxUnits indicates the maximum number of row units or slots available in the power phase
powerPhases = {
    'BareMetal': [{
        'name': 'C',
        'start': 5,
        'end': 20,
        'maxUnits': 16
    },{
        'name': 'B',
        'start': 21,
        'end': 38,
        'maxUnits': 11
    },{
        'name': 'A',
        'start': 39,
        'end': 54,
        'maxUnits': 16
    }],
    # Only allow 2U server, only allow 21 per rack
    'NG2': [{
        'name': 'C',
        'start': 5,
        'end': 20,
        'maxUnits': 16
    },{
        'name': 'B',
        'start': 21,
        'end': 38,
        'maxUnits': 12
    },{
        'name': 'A',
        'start': 39,
        'end': 54,
        'maxUnits': 16
    }],
    'NG3': [{
        'name': 'C',
        'start': 5,
        'end': 20,
        'maxUnits': 16
    },{
        'name': 'B',
        'start': 21,
        'end': 38,
        'maxUnits': 10
    },{
        'name': 'A',
        'start': 39,
        'end': 54,
        'maxUnits': 14
    }]
}

phaseStyles = {
    'NG2': {'align': 'center','valign': 'top','border': 1, 'bg_color': '#F5C4A6'},
    'NG3': {'align': 'center','valign': 'top','border': 1, 'bg_color': '#8EE77F'}
}

# Show the specified error and quit
def showError(error):
    print('\n')
    print(f'\033[91mX\033[0m - {error}')
    sys.exit(-1)

# Get the row in the worksheet for a specific slot
def getRowForSL(sl):
    return sl + 4

# Get the row in the worksheet for a specified slot as a UL with a format like u02
def getRowForUL(ul):
    if ul.lower().startswith('u'):
        return (50 - int(ul.lower()[1:])) + 4
    else:
        showError(f'{ul} is not a valid UL string')

# Generate the Watsonx usage tab in the spreadsheet
def generateElevationTemplate(workbook, worksheet, isHighPower):
    bold = workbook.add_format({'bold': True})
    boldCenter = workbook.add_format({
        'bold': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True
    })

    boldCenterGrey = workbook.add_format({
        'bold': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': '#B7B7B7',
        'border': 1
    })

    lightGray = workbook.add_format()
    lightGray.set_bg_color('#D0CECE')

    mediumGray = workbook.add_format()
    mediumGray.set_bg_color('#AEAAAA')

    darkGray = workbook.add_format()
    darkGray.set_bg_color('#757171')

    yellow = workbook.add_format()
    yellow.set_bg_color('#FFE699')

    black = workbook.add_format()
    black.set_bg_color('#000000')

    green = workbook.add_format({'align': 'center','valign': 'vcenter','border': 1})
    green.set_bg_color('#87C653')

    cyan = workbook.add_format({'align': 'center','valign': 'vcenter','border': 1})
    cyan.set_bg_color('#22A6E9')

    beige = workbook.add_format({'align': 'center','valign': 'vcenter','border': 1})
    beige.set_bg_color('#F5C4A6')

    gen3Switches = workbook.add_format({'align': 'center','valign': 'vcenter','border': 1})
    gen3Switches.set_bg_color('#EBD48D')

    filler = workbook.add_format({'align': 'center','valign': 'vcenter','border': 1})
    filler.set_bg_color('#C65911')

    worksheet.write('C4', 'SL')
    worksheet.write('D4', 'S')
    if rackType == 'BareMetal':
        worksheet.write('B4', 'Phase')
        worksheet.write('D4', 'RUs')

    if not isHighPower:
        worksheet.write('E4', 'PDU Mapping', bold)

        # Write out the phase labels
        i = 4
        while i <= 19:
            worksheet.write(i, 1, 'C', lightGray)
            i += 1
        while i <= 37:
            worksheet.write(i, 1, 'B', mediumGray)
            i += 1
        while i <= 53:
            worksheet.write(i, 1, 'A', lightGray)
            i += 1

    # Write out the slot numbers going down
    i = 4
    while i <= 53:
        worksheet.write_number(i, 2, i - 3)
        i += 1

    # Write out the slot numbers going up
    i = 4
    while i <= 53:
        worksheet.write_number(i, 3, (50 - i) + 4)
        i += 1

    if not isHighPower:
        # Write out the PDU Mapping
        i = 4
        while i <= 19:
            if i % 2 == 0:
                worksheet.write(i, 4, f'D{(50 - i) + 2}', lightGray)
            else:
                worksheet.write(i, 4, '', lightGray)
            i += 1

        while i <= 37:
            if i % 2 == 0:
                worksheet.write(i, 4, f'D{(50 - i) + 2}', mediumGray)
            else:
                worksheet.write(i, 4, '', mediumGray)
            i += 1
        while i <= 53:
            if i % 2 == 0:
                worksheet.write(i, 4, f'D{(50 - i) + 2}', darkGray)
            else:
                worksheet.write(i, 4, '', darkGray)
            i += 1

        # Write out the PDU Mapping - part 2
        i = 4
        while i <= 19:
            if i % 2 == 0:
                worksheet.write(i, 5, f'U{i - 3}', lightGray)
            else:
                worksheet.write(i, 5, '', lightGray)
            i += 1

        while i <= 37:
            if i % 2 == 0:
                worksheet.write(i, 5, f'U{i - 3}', mediumGray)
            else:
                worksheet.write(i, 5, '', mediumGray)
            i += 1
        while i <= 53:
            if i % 2 == 0:
                worksheet.write(i, 5, f'U{i - 3}', darkGray)
            else:
                worksheet.write(i, 5, '', darkGray)
            i += 1

    # Now we fill in the specific values for the rack type
    if isHighPower:
        worksheet.set_column(f'E:E', 35)
    elif rackType == 'BareMetal':
        worksheet.set_column(f'G:G', 35)
#        worksheet.merge_range(f'G{getRowForSL(21)}:G{getRowForSL(22)}', 'TOR2 (DCS-7050CX3-64-R)', boldCenter)
#        worksheet.merge_range(f'G{getRowForSL(23)}:G{getRowForSL(24)}', 'TOR1 (DCS-7050CX3-64-R)', boldCenter)
#        worksheet.write(f'G{getRowForSL(25)}', 'MTOR2 (DCS-7010T-48-R)', boldCenter)
#        worksheet.write(f'G{getRowForSL(26)}', 'MTOR1 (DCS-7010T-48-R)', boldCenter)
#        worksheet.write(f'G{getRowForSL(27)}', 'Cable Pass Thru', boldCenterGrey)
    elif rackType == 'NG2':
        worksheet.set_column(f'G:G', 35)
#        worksheet.merge_range(f'G{getRowForSL(25)}:G{getRowForSL(26)}', 'TOR2\nARISTA DCS-7260CX3-64-r', green)
#        worksheet.merge_range(f'G{getRowForSL(27)}:G{getRowForSL(28)}', 'TOR1\nARISTA DCS-7260CX3-64-r', green)
#        worksheet.write(f'G{getRowForSL(29)}', 'MTOR2;  ARISTA DCS-7010TX-48-R', boldCenter)
#        worksheet.write(f'G{getRowForSL(30)}', 'MTOR1;  ARISTA DCS-7010TX-48-R', cyan)
    elif rackType == 'NG3':
        # NG3 racks have an additional column for the server population order.  We also have extra
        # blackout slots.
        worksheet.write(f'G4', 'Server Population Order', boldCenter)
        worksheet.set_column(f'G:G', 14)
        worksheet.set_row(3, 35)
        worksheet.merge_range(f'G{getRowForSL(25)}:G{getRowForSL(30)}', ' ', black)
        worksheet.write(f'G{getRowForSL(35)}', ' ', black)

        serverPopulationOrder = {
            1: 20,
            3: 10,
            5: 18,
            7: 7,
            9: 15,
            11: 4,
            13: 13,
            15: 1,
            17: 17,
            19: 9,
            23: 6,
            31: 12,
            33: 3,
            37: 11,
            39: 19,
            41: 8,
            43: 16,
            45: 5,
            47: 14,
            49: 2
        }

        for s in serverPopulationOrder:
            worksheet.merge_range(f'G{getRowForSL(s)}:G{getRowForSL(s+1)}', serverPopulationOrder[s], boldCenter)

        worksheet.set_column(f'H:H', 35)
#        worksheet.write(f'H{getRowForSL(30)}', 'MTOR1; ARISTA DCS-7010T-48-R', gen3Switches)
#        worksheet.write(f'H{getRowForSL(29)}', 'MTOR2; ARISTA DCS-7010T-48-R', gen3Switches)
#        worksheet.write(f'H{getRowForSL(22)}', 'leave empty', boldCenter)
#        worksheet.merge_range(f'H{getRowForSL(21)}:H{getRowForSL(23)}', 'leave empty', boldCenter)
#        worksheet.merge_range(f'H{getRowForSL(27)}:H{getRowForSL(28)}', 'TOR2\nARISTA DCS-7260CX3-64-R', gen3Switches)
#        worksheet.merge_range(f'H{getRowForSL(25)}:H{getRowForSL(26)}', 'TOR1\nARISTA DCS-7260CX3-64-R', gen3Switches)
#        worksheet.write(f'H{getRowForSL(29)}', 'OPEN - Cable Passthrough', boldCenter)
#        worksheet.write(f'H{getRowForSL(35)}', 'OPEN - Cable Passthrough', boldCenter)
#        worksheet.write(f'H{getRowForSL(36)}', 'Filler', filler)



# Find the max power value for the solution with the specified ID
def findMaxPower(id, solutions):
    if id in solutions:
        solution = solutions[id]
        for server in solution['server_configurations']:
            if 'max_power' in server:
                return server['max_power']
    showError(f'Unable to find max_power for {id}.  We can\'t add a server to a rack without knowing the power consumption.')

# Find the rack units for the component used by the solution with the specified ID
def findRackUnits(id, solutions, components):
    if id in solutions:
        solution = solutions[id]
        for server in solution['server_configurations']:
            if server['id'] in components:
                component = components[server['id']]
                if 'rack_units' in component:
                    return component['rack_units']

    showError(f'Unable to find rack units for {id}')

# Combine the data in the servers, solutions, and components into individual server
# objects that contain the rack units and max power
def combineServerData(serverCounts, solutions, components):
    servers = []
    for j,id in enumerate(serverCounts):
        # We need to know the power consumption of the servers in the rack so we can
        # populate the rack with the highest power consumption at the bottom of the power
        # phase.  However, not all server specifications have the power consumption
        # filled in.
        #
        # If we're building a rack with just one type of server then we don't need the
        # power consumption since they're all the same.  If the rack has two or more types
        # of servers then we need to get the power consumption value for every server or
        # we'll throw an error.
        if len(serverCounts) == 1:
            maxPower = 999
        else:
            maxPower = findMaxPower(id, solutions)
        rackUnits = findRackUnits(id, solutions, components)
        i = 0
        while i < serverCounts[id]:
            server = {}
            server['id'] = id
            server['max_power'] = maxPower
            server['rack_units'] = rackUnits
            server['color'] = COLORS[j]
            servers.append(server)

            i += 1

    return servers

# We sort servers by max_power
def serverHash(server):
    return server['max_power']

# Read in the server spec JSON file
def readServers(path):
    if not os.path.isfile(path):
        showError(f'Unable to find file {path}')

    with open(path) as f:
        data = json.load(f)
        if 'servers' in data:
            return data['servers']
        else:
            showError('The servers value is required in the server specification.')

# Read the rack class from the server config
def readRackClass(path):
    if not os.path.isfile(path):
        showError(f'Unable to find file {path}')

    with open(path) as f:
        data = json.load(f)
        if 'rackClass' in data:
            return data['rackClass']
        else:
            showError('The rackClass value is required in the server specification.')

# Join a path with two subfolders into a single path
def joinPath(folder, subFolder, subFolder2):
    return os.path.join(os.path.join(folder, subFolder), subFolder2)

# This function returns True if the specified server is allowed in either the prod or
# dev sections of the allowed server classes in the rack specification.
def isInProdOrDevArray(server, serverClass):
    if 'class' in serverClass and 'prod' in serverClass['class'] and serverClass['class']['prod'] is not None:
        if server in serverClass['class']['prod']:
            return True
    if 'class' in serverClass and 'dev' in serverClass['class'] and serverClass['class']['dev'] is not None:
        if server in serverClass['class']['dev']:
            return True

    return False

# Return the total number of servers allowed in the rack according to the rack specification
def countAllowedServers(server, rackSpec):
    count = 0
    serverClasses = rackSpec['racking']
    for serverClass in serverClasses:
        if serverClass['type'] == 'server':
            if isInProdOrDevArray(server, serverClass):
                count += 1
    return count

# This function gathers all of the servers that are allowed in the rack spec,
# checks each of the requested servers to see if they're allowed, and throws
# an error with all of the servers that aren't allowed if any are found.
def validateServerClasses(servers, rackSpec):
    allowedServerCount = 0
    allowedServers = []
    serverClasses = rackSpec['racking']
    for serverClass in serverClasses:
        if serverClass['type'] == 'server':
            allowedServerCount += 1
            if 'class' in serverClass and 'prod' in serverClass['class'] and serverClass['class']['prod'] is not None:
                for sc in serverClass['class']['prod']:
                    if sc not in allowedServers:
                        allowedServers.append(sc)
            if 'class' in serverClass and 'dev' in serverClass['class'] and serverClass['class']['dev'] is not None:
                for sc in serverClass['class']['dev']:
                    if sc not in allowedServers:
                        allowedServers.append(sc)

    notAllowed = []
    requestedServerCount = 0
    for server in servers:
        requestedServerCount = requestedServerCount + servers[server]
        if not server in allowedServers:
            notAllowed.append(server)
    if len(notAllowed) > 0:
        showError(f'The server types {notAllowed} are not supported in racks of type {rackSpec["rack_qualified_config_type"]}')

    print(f'This rack allows {allowedServerCount} servers')
    if requestedServerCount > allowedServerCount:
        # There are some cases where we don't want to allow as many servers as would fit in the available rack units because
        # of the consumed power or heat.  This extra check makes sure they aren't adding more servers than are allowed based
        # on the rack specification.
        showError(f'This rack type only allows {allowedServerCount} servers and the server config is for {requestedServerCount} servers.')

    for server in servers:
        # Some rack speccs allow a smaller number of a specific type of server so we check
        # for that too.
        if servers[server] > countAllowedServers(server, rackSpec):
            showError(f'The server specification requests {servers[server]} servers of type {server}, but this rack specification only allows {countAllowedServers(server, rackSpec)} servers.')

# This function loads the rack spec from platform-inventory or throws an error if the rack spec
# can't be found.
def loadRackSpec(rackClass):
    path = os.path.join(joinPath(piPath, 'specifications', 'racks'), f'{rackClass}.yaml')
    if not os.path.isfile(path):
        showError(f'Unable to find file {path} for rack class {rackClass}')

    with open(path) as f:
        data = yaml.safe_load(f)
        return data


# Load the server solutions from platform-inventory
def loadServerSolutions(path):
    loadedSolutions = {}
    solutions = []
    path = joinPath(path, 'specifications', 'solutions')
    dirs = []
    for (dirpath, dirnames, filenames) in walk(path):
        dirs.extend(dirnames)
        break

    for dirname in dirs:
        files = []
        for (dirpath, dirnames, filenames) in walk(os.path.join(path, dirname)):
            files.extend(filenames)
            break
        for file in files:
            solutions.append(joinPath(path, dirname, file))

    for solution in solutions:
        if solution.endswith('.yaml'):
            with open(solution) as f:
                data = yaml.safe_load(f)
                loadedSolutions[data['name']] = data

    return loadedSolutions

# Load the server components data from platform-inventory
def loadServerComponents(path):
    loadedComponents = {}
    components = []
    path = joinPath(path, 'specifications', 'components')
    for (dirpath, dirnames, filenames) in walk(path):
        components.extend(filenames)
        break

    for component in components:
        if component.endswith('.yaml'):
            with open(os.path.join(path, component)) as f:
                data = yaml.safe_load(f)
                for server in data['components']:
                    loadedComponents[server['id']] = server

    return loadedComponents

# Takes the set of servers and validates if there's space for them.
def validateServers(servers):
    # We oversubscribe almost all of our racks on power.  That means if all servers operated
    # at max power we'd be way over the allowed power consumption.  We need to support that in
    # the tool which means that we can't really validate power consumption on a rack.  We need
    # to figure out a better way to manage this.  TODO
    maxRackPower = 50 * 1000

    power = 0
    for server in servers:
        power += server['max_power']

    if power > maxRackPower:
        showError(f'The rack power total of {power} exceeds the max allowed power for the rack of {maxRackPower}')
    else:
        print(f'Total rack power: {power}')

    rackUnits = 0
    for server in servers:
        rackUnits += server['rack_units']

    maxRackUnits = 0

# This is really tricky.  We need to know the role of the server for the server allocation,
# but there's no way for us to know that for a lot of the compute nodes.  We default to compute
# and it would need to get fixed up later.  TODO
def getServerRole():
    if rackType == 'BareMetal':
        return 'vpc_bare_metal'
    elif rackType == 'NG2':
        # TODO: This doesn't cover servers that are edge or control.  We need to think if a way to handle those.
        return 'vpc_compute'
    elif rackType == 'NG3':
        # TODO: This doesn't cover servers that are edge or control.  We need to think if a way to handle those.
        return 'vpc_compute'
    else:
        showError(f'The rack type {rackType} is not supported')

# Returns True if the specified id is allowed in the specified position and false otherwise
def isIdInPosition(id, position):
    if 'prod' in position['class'] and position['class']['prod'] and id in position['class']['prod']:
        return True
    if 'dev' in position['class'] and position['class']['dev'] and id in position['class']['dev']:
        return True
    return False    

# Returns True if a sever in the specified slot taking up the specified number of rack units
# would overlap an existing server in the elevation and False otherwise.
def isOverlappingUsedUnits(slot, units, phase):
    i = 0
    while i <= units:
        if slot + i in phase['usedUnits']:
            return True
        i += 1

    return False

# This function attempts to place a server in the next correct open position based on the
# available positions from the rack specification.
def placeServer(server, phase, workbook, worksheet, phases, serversYaml, style=None, col='G'):
    tries = 0
    while tries < 3:
        currentPhase = (phase + tries) % 3
#        print(f'currentPhase: {currentPhase}')
        for slot in phases[currentPhase]['positionsArray']:
            if 'usedUnits' not in phases[currentPhase]:
                phases[currentPhase]['usedUnits'] = []

#            print(f'Trying slot {slot}')
            position = phases[currentPhase]['allowedPositions'][slot]
            units = server['rack_units'] - 1
#            print(f"isIdInPosition(server['id'], position): {isIdInPosition(server['id'], position)}")
            if isIdInPosition(server['id'], position) and 'used' not in position and not isOverlappingUsedUnits(slot, units, phases[currentPhase]):
                print(f'Placing server {server["id"]} in power phase {phases[currentPhase]["name"]} at {position["position"]}')
                # This means we found a good place for this server
                position['used'] = True
                position['serverClass'] = server['id']

                style['bg_color'] = server['color']
                if units == 0:
                    phases[currentPhase]['usedUnits'].append(slot)
                    worksheet.write(f'{col}{slot + 1}', server['id'], workbook.add_format(style))
                else:
                    # We want to mark the rack units we used so we don't overlap a cell here.
                    # Some rack specifications are written in a loose way that would potentially
                    # allow for this.
                    i = 0
                    while i < units:
                        phases[currentPhase]['usedUnits'].append(slot + i)
                        i += 1
                    # For servers that are larger than 1U we show the slot in the cell
                    # to make the elevation easier to read.
                    style['text_wrap'] = True
                    worksheet.merge_range(f'{col}{slot + 1}:{col}{slot + units + 1}',
                                          f"{position['position'].replace('u', 's')}\n{server['id']}",
                                          workbook.add_format(style))

                s = (50 - slot) + 4
                sId = f's{s}'
                if s < 10:
                    sId = f's0{s}'
                serversYaml['values'][sId] = {
                    'state': 'plan',
                    'class': server['id'],
                    'role': getServerRole()
                }
                return

        tries += 1

    # If we get here that means we didn't find a slot for this server.  We normally catch this case with
    # validations against the rack spec, but this can happen if the spec allows invalid configurations.
    print(f'''Unable to find a position for all of the servers.
Server: {server}
Phases: {phases}
    ''')
    showError(f'Unable to find suitable slot for {server}')

# This is a hash function used for sorting power phases.
def phaseHash(phase):
    return phase['name']

# This function populates the servers in the elevation based on the allowed positions in the rack
# specification.
def populatePowerPhasesByRackSpec(servers, workbook, worksheet, phases, rackSpec, style=None, col='G'):
    if style is None:
        style = {'align': 'center','valign': 'top','border': 1}
    else:
        style = style

    serversYaml = {
        'values': {

        }
    }

    # We need to make sure we're sorting the power phases in the correct order
    # so we load the rack from the bottom up.
    phases.sort(key=phaseHash, reverse=False)

    isHighPower = isHighPowerRack(rackSpec)

    for i, server in enumerate(servers):
        # If the rack is a standard power rack then we need to distribute the server across the three power
        # phases so we can an even distribution of power usage across the PDUs.  If this is a high power rack
        # then we just populate the rack from the bottom up since those servers are already cross-cabled
        # across all the power phases.
        #
        # The easiest way to do that is to try to add every server to phase 0 at the bottom of the rack.
        # That will fill up the bottom phase and then bump to the next phase if that one is full and so on
        # until all of the available slots in the rack are filled from the bottom to the top of the rack.
        if isHighPower:
            placeServer(server, 0, workbook, worksheet, phases, serversYaml, style, col)
        else:
            placeServer(server, i % 3, workbook, worksheet, phases, serversYaml, style, col)

    # Some rack specifications list slots as required, but we don't always put servers
    # in those slots.  In that case we put an allocation for the slot indicating that
    # it's open. So we need to look at all of the required slots in the specification
    # and add the open allocations for the ones that don't have servers.
    serverClasses = rackSpec['racking']
    for serverClass in serverClasses:
        if serverClass['type'] == 'server' and serverClass['required']:
            if serverClass['position'].replace('u', 's') not in serversYaml['values']:
                serversYaml['values'][serverClass['position'].replace('u', 's')] = {
                    'state': 'open',
                    'class': 'unknown',
                    'role': 'custom'
                }

    # This YAML file represents the rack information.  It will show each server we're adding to the rack and their position.
    rackYaml = {
        'rack_build_reqs': readServers(serversPath),
        'servers': serversYaml
    }
    with open(outputYamlPath, 'w') as yaml_file:
        yaml.dump(rackYaml, yaml_file, default_flow_style=False)

# We need to get the ID of the switch part.  Right now we're just grabbing the first one.
# We need to get a better representation in the rack spec for the preferred one.
def getSwitchId(rackSpec, name):
    tors = rackSpec['switch_tor']

    for tor in tors:
        if tor['name'] == name:
            return tor['ims_models'][0]

# Load the switch information from the rack spec and add it to the elevation
def populateSwitchesAndCables(rackSpec, workbook, worksheet, style=None, col='G'):
    serverClasses = rackSpec['racking']
    if style is None:
        style = workbook.add_format({'align': 'center','valign': 'vcenter','border': 1})
        style.set_bg_color('#EBD48D')
    else:
        style = workbook.add_format(style)
    for serverClass in serverClasses:
        if serverClass['type'] == 'switch_tor':
            slot = getRowForUL(serverClass['position']) + 1
            name = f"{serverClass['name'].upper()} - {getSwitchId(rackSpec, serverClass['name'])}"
            if serverClass['name'].startswith('mtor'):
                worksheet.write(f'{col}{slot}', name, style)
            else:
                # TODO not all TOR switches are 2U.  We need to get this information from the rack spec
                worksheet.merge_range(f'{col}{slot}:{col}{slot+1}', name, style)
        elif serverClass['type'] == 'cabling' or serverClass['type'] == 'egress':
            slot = getRowForUL(serverClass['position']) + 1
            worksheet.write(f'{col}{slot}', 'OPEN - Cable Passthrough',
                            workbook.add_format({'align': 'center','valign': 'vcenter','border': 1}))

# Add the legend to the bottom of the sheet.  The legend shows
# how many servers there are of each type in one easy to see place
# which make it easy to grab the gear when loading the rack.
def addLegend(serverCounts, workbook, worksheet, col=5):
    style = workbook.add_format({'border': 1, 'font_size': 18})

    row = 61
    # Start with showing the header for the legend table.
    worksheet.write_string(row - 1, col, 'Qty', style)
    worksheet.write_string(row - 1, col + 1, 'Config', style)

    for i,server in enumerate(serverCounts):
        worksheet.write_number(row + i, col, int(serverCounts[server]), style)
        worksheet.write_string(row + i, col + 1, server, workbook.add_format({'border': 1, 'font_size': 18, 'bg_color': COLORS[i]}))

# Add a specific allowed position to the correct power phase
def addAllowedPosition(phases, position):
    slot = getRowForUL(position['position'])

    for phase in phases:
        start = phase['start']
        end = phase['end']
        if 'allowedPositions' not in phase:
            phase['allowedPositions'] = {}

        if slot + 1 >= start and slot < end:
            phase['allowedPositions'][slot] = position

# We need to load all of the power phases with the allowed slots from the rack specification
def loadPowerPhaseData(phases, rackSpec):
    serverClasses = rackSpec['racking']
    for serverClass in serverClasses:
        if serverClass['type'] == 'server':
            addAllowedPosition(phases, serverClass)

    for phase in phases:
        if 'allowedPositions' in phase:
            keys = list(phase['allowedPositions'].keys())
            keys.sort(reverse=True)
            phase['positionsArray'] = keys

# Return True if this is a high power rack and False otherwise.
# Most racks are low power meaning that they use the standard STV-4523G/SB PDU.
# That means we need to load them based on the evenly distributing to the
# three power phases.  However, GPU racks and other high powered servers use
# other PDU models like C2W36TE-GPAE2M99/SA.  In that case the power phases
# are more distributed over the very low number of servers in the rack and we just
# load the rack from the bottom up.
def isHighPowerRack(rackSpec):
    for pdu in rackSpec['pdus']:
        if pdu['name'] == 'pdu_1' and len(pdu['ims_models']) > 0 and pdu['ims_models'][0] == 'STV-4523G/SB':
            # Then this is the standard PDU which means this is a low powered rack
            print('Standard power PDU rack with PDU STV-4523G/SB. Loading all power phases equally.')
            return False
        elif pdu['name'] == 'pdu_1' and len(pdu['ims_models']) > 0:
            print(f'High power PDU rack with PDU {pdu["ims_models"][0]}. Building the rack from the bottom up.')
            return True
        else:
            showError('Unable to find the PDU type for specified rack class')

# This is the main entry point where we load all the data, validate it, and build the elevation.
def buildElevation():
    # The first step is to load the list of requested servers
    serverList = readServers(serversPath)

    # Then we need to load the rack specification so we know how to build the rack
    rackSpec = loadRackSpec(readRackClass(serversPath))

    # We need to determine if this is a high power rack or not
    isHighPower = isHighPowerRack(rackSpec)

    # Now we do the first validation of the requested servers are allowed in the rack
    validateServerClasses(serverList, rackSpec)

    # Then we load the server data and combine it all together.
    servers = combineServerData(serverList, loadServerSolutions(piPath), loadServerComponents(piPath))

    # Then we sort the servers by max_power so we add the servers that take the largest
    # amount of power first.
    servers.sort(key=serverHash, reverse=True)

    # Then we do an extra validation of servers by power consumption and rack units
    validateServers(servers)

    # At this point we know the servers are sorted, we have all the data, and this is valid.  Now we're ready to build the elevation.
    workbook = xlsxwriter.Workbook(f'{outputPath}')
    worksheet = workbook.add_worksheet('Elevation')
    generateElevationTemplate(workbook, worksheet, isHighPower)

    if isHighPower:
        addLegend(serverList, workbook, worksheet, col=3)
        loadPowerPhaseData(powerPhases['NG2'], rackSpec)
        populateSwitchesAndCables(rackSpec, workbook, worksheet, col='E')
        populatePowerPhasesByRackSpec(servers, workbook, worksheet, powerPhases['NG2'], rackSpec, phaseStyles['NG2'], col='E')
    elif rackType == 'BareMetal':
        addLegend(serverList, workbook, worksheet)
        loadPowerPhaseData(powerPhases['BareMetal'], rackSpec)
        populateSwitchesAndCables(rackSpec, workbook, worksheet)
        populatePowerPhasesByRackSpec(servers, workbook, worksheet, powerPhases['BareMetal'], rackSpec)
    elif rackType == 'NG2':
        addLegend(serverList, workbook, worksheet)
        loadPowerPhaseData(powerPhases['NG2'], rackSpec)
        populateSwitchesAndCables(rackSpec, workbook, worksheet)
        populatePowerPhasesByRackSpec(servers, workbook, worksheet, powerPhases['NG2'], rackSpec, phaseStyles['NG2'])
    elif rackType == 'NG3':
        addLegend(serverList, workbook, worksheet, col=6)
        loadPowerPhaseData(powerPhases['NG3'], rackSpec)
        populateSwitchesAndCables(rackSpec, workbook, worksheet, col='H')
        populatePowerPhasesByRackSpec(servers, workbook, worksheet, powerPhases['NG3'], rackSpec, style=phaseStyles['NG3'], col='H')


    workbook.close()


buildElevation()