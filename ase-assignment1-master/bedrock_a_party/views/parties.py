from flakon import JsonBlueprint
from flask import abort, json, jsonify, request
from flask.helpers import make_response

from bedrock_a_party.classes.party import CannotPartyAloneError, Party, NotInvitedGuestError, ItemAlreadyInsertedByUser, NotExistingFoodError

parties = JsonBlueprint('parties', __name__)

_LOADED_PARTIES = {}  # dict of available parties
_PARTY_NUMBER = 0  # index of the last created party

#
# These are utility functions. Use them, DON'T CHANGE THEM!!
#
# the function exists_party() presented an error in thee first if condition: > needed to be substituted with >=
#

def create_party(req):
    global _LOADED_PARTIES, _PARTY_NUMBER

    # get data from request
    json_data = req.get_json()

    # list of guests
    try:
        guests = json_data['guests']
    except:
        raise CannotPartyAloneError("you cannot party alone!")

    # add party to the loaded parties lists
    _LOADED_PARTIES[str(_PARTY_NUMBER)] = Party(_PARTY_NUMBER, guests)
    _PARTY_NUMBER += 1

    return jsonify({'party_number': _PARTY_NUMBER - 1})


def get_all_parties():
    global _LOADED_PARTIES

    return jsonify(loaded_parties=[party.serialize() for party in _LOADED_PARTIES.values()])


def exists_party(_id):
    global _PARTY_NUMBER
    global _LOADED_PARTIES

    if int(_id) > _PARTY_NUMBER:
        abort(404)  # error 404: Not Found, i.e. wrong URL, resource does not exist
    elif not(_id in _LOADED_PARTIES):
        abort(410)  # error 410: Gone, i.e. it existed but it's not there anymore


@parties.route("/parties", methods=['POST', 'GET'])
def all_parties():
    result = None
    if request.method == 'POST':
        try:
            result = create_party(request) # the function creates a party and returns its ID 
        except CannotPartyAloneError as e:
            abort(400, str(e)) # error bad request

    elif request.method == 'GET':
        result = get_all_parties()

    return result


@parties.route("/parties/loaded", methods=['GET'])
def loaded_parties():
    global _LOADED_PARTIES
    return jsonify(loaded_parties = len(_LOADED_PARTIES))


@parties.route("/party/<id>", methods=['GET', 'DELETE'])
def single_party(id):
    global _LOADED_PARTIES
    result = ""

    exists_party(id)
    
    if 'GET' == request.method:
        for party in _LOADED_PARTIES.values():
            if party.id == int(id): # retrieve the party with the same id in the GET request
                result = party.serialize()
                break

    elif 'DELETE' == request.method:
        result = _LOADED_PARTIES[id].serialize() # save the party to be returned
        _LOADED_PARTIES.pop(id) # remove the element from the dictionary

    return result


@parties.route("/party/<id>/foodlist", methods=['GET'])
def get_foodlist(id):
    global _LOADED_PARTIES
    result = ""

    exists_party(id)
    
    if 'GET' == request.method:
        result = jsonify(foodlist = _LOADED_PARTIES[id].get_food_list().serialize())
        # the foodlist is retrieved from the party _LOADED_PARTIES[id] using the method
        # get_food_list(). This method will return a FoodList object, so it must be serialized
        # to obtain a list of Food serialized objects. Finally, the jsonify() function is applied
        # to convert the array into json format
        
    return result


@parties.route("/party/<id>/foodlist/<user>/<item>", methods=['POST', 'DELETE'])
def edit_foodlist(id, user, item):
    global _LOADED_PARTIES

    exists_party(id)

    # retrieve the party given the specific id
    party = _LOADED_PARTIES[id]

    result = ""

    if 'POST' == request.method:
        # add the item to the food-list
        # the check if the user has been invited and if the food has already been inserted is done inside the add_to_food_list() method 
        # this method returns a Food object, which must be serialized. Finally, jsonify() is called to convert the python object into json
        try:
            result = jsonify(party.add_to_food_list(item, user).serialize())
        except NotInvitedGuestError as e1:
            abort(401, str(e1))
        except ItemAlreadyInsertedByUser as e2:
            abort(400, str(e2))

    if 'DELETE' == request.method:        
        # remove the item to the food-list
        # the check if the user has not added food to the party is inside the remove() method of the Food class, called inside 
        # the remove_from_food_list() method in the Party class
        try:
            party.remove_from_food_list(item, user)
            result = jsonify(msg = "Food deleted!")
        except NotExistingFoodError as e:
            abort(400, str(e))

    return result
