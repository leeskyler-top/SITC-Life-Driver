from utils.js2py.pyjs import *

# setting scope
var = Scope(JS_BUILTINS)
set_global_object(var)

# Code follows:
var.registers(['strToBt', 'getKeyBytes', 'initPermute', 'finallyPermute', 'hexToBt64', 'pPermute', 'expandPermute',
               'getBoxBinary', 'xor', 'generateKeys', 'enc', 'bt4ToHex', 'hexToBt4', 'strEnc', 'sBoxPermute',
               'bt64ToHex', 'dec', 'strDec', 'byteToString'])


@Js
def PyJsHoisted_strEnc_(data, firstKey, secondKey, thirdKey, this, arguments, var=var):
    var = Scope({'data': data, 'firstKey': firstKey, 'secondKey': secondKey, 'thirdKey': thirdKey, 'this': this,
                 'arguments': arguments}, var)
    var.registers(
        ['encByte', 'bt', 'thirdKey', 'firstKeyBt', 'remainderData', 'data', 'i', 'firstKey', 'y', 'iterator', 'tempBt',
         'thirdLength', 'thirdKeyBt', 'encData', 'secondLength', 'secondKeyBt', 'firstLength', 'tempByte', 'leng', 'x',
         'remainder', 'tempData', 'z', 'secondKey'])
    var.put('leng', var.get('data').get('length'))
    var.put('encData', Js(''))
    if ((var.get('firstKey') != var.get(u"null")) and (var.get('firstKey') != Js(''))):
        var.put('firstKeyBt', var.get('getKeyBytes')(var.get('firstKey')))
        var.put('firstLength', var.get('firstKeyBt').get('length'))
    if ((var.get('secondKey') != var.get(u"null")) and (var.get('secondKey') != Js(''))):
        var.put('secondKeyBt', var.get('getKeyBytes')(var.get('secondKey')))
        var.put('secondLength', var.get('secondKeyBt').get('length'))
    if ((var.get('thirdKey') != var.get(u"null")) and (var.get('thirdKey') != Js(''))):
        var.put('thirdKeyBt', var.get('getKeyBytes')(var.get('thirdKey')))
        var.put('thirdLength', var.get('thirdKeyBt').get('length'))
    if (var.get('leng') > Js(0.0)):
        if (var.get('leng') < Js(4.0)):
            var.put('bt', var.get('strToBt')(var.get('data')))
            if ((((((var.get('firstKey') != var.get(u"null")) and (var.get('firstKey') != Js(''))) and (
                    var.get('secondKey') != var.get(u"null"))) and (var.get('secondKey') != Js(''))) and (
                         var.get('thirdKey') != var.get(u"null"))) and (var.get('thirdKey') != Js(''))):
                var.put('tempBt', var.get('bt'))
                # for JS loop
                var.put('x', Js(0.0))
                while (var.get('x') < var.get('firstLength')):
                    var.put('tempBt', var.get('enc')(var.get('tempBt'), var.get('firstKeyBt').get(var.get('x'))))
                    # update
                    (var.put('x', Js(var.get('x').to_number()) + Js(1)) - Js(1))
                # for JS loop
                var.put('y', Js(0.0))
                while (var.get('y') < var.get('secondLength')):
                    var.put('tempBt', var.get('enc')(var.get('tempBt'), var.get('secondKeyBt').get(var.get('y'))))
                    # update
                    (var.put('y', Js(var.get('y').to_number()) + Js(1)) - Js(1))
                # for JS loop
                var.put('z', Js(0.0))
                while (var.get('z') < var.get('thirdLength')):
                    var.put('tempBt', var.get('enc')(var.get('tempBt'), var.get('thirdKeyBt').get(var.get('z'))))
                    # update
                    (var.put('z', Js(var.get('z').to_number()) + Js(1)) - Js(1))
                var.put('encByte', var.get('tempBt'))
            else:
                if ((((var.get('firstKey') != var.get(u"null")) and (var.get('firstKey') != Js(''))) and (
                        var.get('secondKey') != var.get(u"null"))) and (var.get('secondKey') != Js(''))):
                    var.put('tempBt', var.get('bt'))
                    # for JS loop
                    var.put('x', Js(0.0))
                    while (var.get('x') < var.get('firstLength')):
                        var.put('tempBt', var.get('enc')(var.get('tempBt'), var.get('firstKeyBt').get(var.get('x'))))
                        # update
                        (var.put('x', Js(var.get('x').to_number()) + Js(1)) - Js(1))
                    # for JS loop
                    var.put('y', Js(0.0))
                    while (var.get('y') < var.get('secondLength')):
                        var.put('tempBt', var.get('enc')(var.get('tempBt'), var.get('secondKeyBt').get(var.get('y'))))
                        # update
                        (var.put('y', Js(var.get('y').to_number()) + Js(1)) - Js(1))
                    var.put('encByte', var.get('tempBt'))
                else:
                    if ((var.get('firstKey') != var.get(u"null")) and (var.get('firstKey') != Js(''))):
                        var.put('x', Js(0.0))
                        var.put('tempBt', var.get('bt'))
                        # for JS loop
                        var.put('x', Js(0.0))
                        while (var.get('x') < var.get('firstLength')):
                            var.put('tempBt',
                                    var.get('enc')(var.get('tempBt'), var.get('firstKeyBt').get(var.get('x'))))
                            # update
                            (var.put('x', Js(var.get('x').to_number()) + Js(1)) - Js(1))
                        var.put('encByte', var.get('tempBt'))
            var.put('encData', var.get('bt64ToHex')(var.get('encByte')))
        else:
            var.put('iterator', var.get('parseInt')((var.get('leng') / Js(4.0))))
            var.put('remainder', (var.get('leng') % Js(4.0)))
            var.put('i', Js(0.0))
            # for JS loop
            var.put('i', Js(0.0))
            while (var.get('i') < var.get('iterator')):
                var.put('tempData', var.get('data').callprop('substring', ((var.get('i') * Js(4.0)) + Js(0.0)),
                                                             ((var.get('i') * Js(4.0)) + Js(4.0))))
                var.put('tempByte', var.get('strToBt')(var.get('tempData')))

                if ((((((var.get('firstKey') != var.get(u"null")) and (var.get('firstKey') != Js(''))) and (
                        var.get('secondKey') != var.get(u"null"))) and (var.get('secondKey') != Js(''))) and (
                             var.get('thirdKey') != var.get(u"null"))) and (var.get('thirdKey') != Js(''))):

                    var.put('tempBt', var.get('tempByte'))
                    # for JS loop
                    var.put('x', Js(0.0))
                    while (var.get('x') < var.get('firstLength')):
                        var.put('tempBt', var.get('enc')(var.get('tempBt'), var.get('firstKeyBt').get(var.get('x'))))
                        # update
                        (var.put('x', Js(var.get('x').to_number()) + Js(1)) - Js(1))
                    # for JS loop
                    var.put('y', Js(0.0))
                    while (var.get('y') < var.get('secondLength')):
                        var.put('tempBt', var.get('enc')(var.get('tempBt'), var.get('secondKeyBt').get(var.get('y'))))
                        # update
                        (var.put('y', Js(var.get('y').to_number()) + Js(1)) - Js(1))
                    # for JS loop
                    var.put('z', Js(0.0))
                    while (var.get('z') < var.get('thirdLength')):
                        var.put('tempBt', var.get('enc')(var.get('tempBt'), var.get('thirdKeyBt').get(var.get('z'))))
                        # update
                        (var.put('z', Js(var.get('z').to_number()) + Js(1)) - Js(1))
                    var.put('encByte', var.get('tempBt'))
                else:
                    if ((((var.get('firstKey') != var.get(u"null")) and (var.get('firstKey') != Js(''))) and (
                            var.get('secondKey') != var.get(u"null"))) and (var.get('secondKey') != Js(''))):

                        var.put('tempBt', var.get('tempByte'))
                        # for JS loop
                        var.put('x', Js(0.0))
                        while (var.get('x') < var.get('firstLength')):
                            var.put('tempBt',
                                    var.get('enc')(var.get('tempBt'), var.get('firstKeyBt').get(var.get('x'))))
                            # update
                            (var.put('x', Js(var.get('x').to_number()) + Js(1)) - Js(1))
                        # for JS loop
                        var.put('y', Js(0.0))
                        while (var.get('y') < var.get('secondLength')):
                            var.put('tempBt',
                                    var.get('enc')(var.get('tempBt'), var.get('secondKeyBt').get(var.get('y'))))
                            # update
                            (var.put('y', Js(var.get('y').to_number()) + Js(1)) - Js(1))
                        var.put('encByte', var.get('tempBt'))
                    else:
                        if ((var.get('firstKey') != var.get(u"null")) and (var.get('firstKey') != Js(''))):

                            var.put('tempBt', var.get('tempByte'))
                            # for JS loop
                            var.put('x', Js(0.0))
                            while (var.get('x') < var.get('firstLength')):
                                var.put('tempBt',
                                        var.get('enc')(var.get('tempBt'), var.get('firstKeyBt').get(var.get('x'))))
                                # update
                                (var.put('x', Js(var.get('x').to_number()) + Js(1)) - Js(1))
                            var.put('encByte', var.get('tempBt'))
                var.put('encData', var.get('bt64ToHex')(var.get('encByte')), '+')
                # update
                (var.put('i', Js(var.get('i').to_number()) + Js(1)) - Js(1))
            if (var.get('remainder') > Js(0.0)):
                var.put('remainderData',
                        var.get('data').callprop('substring', ((var.get('iterator') * Js(4.0)) + Js(0.0)),
                                                 var.get('leng')))
                var.put('tempByte', var.get('strToBt')(var.get('remainderData')))

                if ((((((var.get('firstKey') != var.get(u"null")) and (var.get('firstKey') != Js(''))) and (
                        var.get('secondKey') != var.get(u"null"))) and (var.get('secondKey') != Js(''))) and (
                             var.get('thirdKey') != var.get(u"null"))) and (var.get('thirdKey') != Js(''))):

                    var.put('tempBt', var.get('tempByte'))
                    # for JS loop
                    var.put('x', Js(0.0))
                    while (var.get('x') < var.get('firstLength')):
                        var.put('tempBt', var.get('enc')(var.get('tempBt'), var.get('firstKeyBt').get(var.get('x'))))
                        # update
                        (var.put('x', Js(var.get('x').to_number()) + Js(1)) - Js(1))
                    # for JS loop
                    var.put('y', Js(0.0))
                    while (var.get('y') < var.get('secondLength')):
                        var.put('tempBt', var.get('enc')(var.get('tempBt'), var.get('secondKeyBt').get(var.get('y'))))
                        # update
                        (var.put('y', Js(var.get('y').to_number()) + Js(1)) - Js(1))
                    # for JS loop
                    var.put('z', Js(0.0))
                    while (var.get('z') < var.get('thirdLength')):
                        var.put('tempBt', var.get('enc')(var.get('tempBt'), var.get('thirdKeyBt').get(var.get('z'))))
                        # update
                        (var.put('z', Js(var.get('z').to_number()) + Js(1)) - Js(1))
                    var.put('encByte', var.get('tempBt'))
                else:
                    if ((((var.get('firstKey') != var.get(u"null")) and (var.get('firstKey') != Js(''))) and (
                            var.get('secondKey') != var.get(u"null"))) and (var.get('secondKey') != Js(''))):

                        var.put('tempBt', var.get('tempByte'))
                        # for JS loop
                        var.put('x', Js(0.0))
                        while (var.get('x') < var.get('firstLength')):
                            var.put('tempBt',
                                    var.get('enc')(var.get('tempBt'), var.get('firstKeyBt').get(var.get('x'))))
                            # update
                            (var.put('x', Js(var.get('x').to_number()) + Js(1)) - Js(1))
                        # for JS loop
                        var.put('y', Js(0.0))
                        while (var.get('y') < var.get('secondLength')):
                            var.put('tempBt',
                                    var.get('enc')(var.get('tempBt'), var.get('secondKeyBt').get(var.get('y'))))
                            # update
                            (var.put('y', Js(var.get('y').to_number()) + Js(1)) - Js(1))
                        var.put('encByte', var.get('tempBt'))
                    else:
                        if ((var.get('firstKey') != var.get(u"null")) and (var.get('firstKey') != Js(''))):

                            var.put('tempBt', var.get('tempByte'))
                            # for JS loop
                            var.put('x', Js(0.0))
                            while (var.get('x') < var.get('firstLength')):
                                var.put('tempBt',
                                        var.get('enc')(var.get('tempBt'), var.get('firstKeyBt').get(var.get('x'))))
                                # update
                                (var.put('x', Js(var.get('x').to_number()) + Js(1)) - Js(1))
                            var.put('encByte', var.get('tempBt'))
                var.put('encData', var.get('bt64ToHex')(var.get('encByte')), '+')
    return var.get('encData')


PyJsHoisted_strEnc_.func_name = 'strEnc'
var.put('strEnc', PyJsHoisted_strEnc_)


@Js
def PyJsHoisted_strDec_(data, firstKey, secondKey, thirdKey, this, arguments, var=var):
    var = Scope({'data': data, 'firstKey': firstKey, 'secondKey': secondKey, 'thirdKey': thirdKey, 'this': this,
                 'arguments': arguments}, var)
    var.registers(
        ['thirdKey', 'firstKeyBt', 'intByte', 'data', 'i', 'decStr', 'decByte', 'strByte', 'firstKey', 'y', 'iterator',
         'tempBt', 'thirdLength', 'thirdKeyBt', 'secondLength', 'secondKeyBt', 'firstLength', 'leng', 'j', 'tempData',
         'x', 'z', 'secondKey'])
    var.put('leng', var.get('data').get('length'))
    var.put('decStr', Js(''))

    if ((var.get('firstKey') != var.get(u"null")) and (var.get('firstKey') != Js(''))):
        var.put('firstKeyBt', var.get('getKeyBytes')(var.get('firstKey')))
        var.put('firstLength', var.get('firstKeyBt').get('length'))
    if ((var.get('secondKey') != var.get(u"null")) and (var.get('secondKey') != Js(''))):
        var.put('secondKeyBt', var.get('getKeyBytes')(var.get('secondKey')))
        var.put('secondLength', var.get('secondKeyBt').get('length'))
    if ((var.get('thirdKey') != var.get(u"null")) and (var.get('thirdKey') != Js(''))):
        var.put('thirdKeyBt', var.get('getKeyBytes')(var.get('thirdKey')))
        var.put('thirdLength', var.get('thirdKeyBt').get('length'))
    var.put('iterator', var.get('parseInt')((var.get('leng') / Js(16.0))))
    var.put('i', Js(0.0))
    # for JS loop
    var.put('i', Js(0.0))
    while (var.get('i') < var.get('iterator')):
        var.put('tempData', var.get('data').callprop('substring', ((var.get('i') * Js(16.0)) + Js(0.0)),
                                                     ((var.get('i') * Js(16.0)) + Js(16.0))))
        var.put('strByte', var.get('hexToBt64')(var.get('tempData')))
        var.put('intByte', var.get('Array').create(Js(64.0)))
        var.put('j', Js(0.0))
        # for JS loop
        var.put('j', Js(0.0))
        while (var.get('j') < Js(64.0)):
            var.get('intByte').put(var.get('j'), var.get('parseInt')(
                var.get('strByte').callprop('substring', var.get('j'), (var.get('j') + Js(1.0)))))
            # update
            (var.put('j', Js(var.get('j').to_number()) + Js(1)) - Js(1))

        if ((((((var.get('firstKey') != var.get(u"null")) and (var.get('firstKey') != Js(''))) and (
                var.get('secondKey') != var.get(u"null"))) and (var.get('secondKey') != Js(''))) and (
                     var.get('thirdKey') != var.get(u"null"))) and (var.get('thirdKey') != Js(''))):

            var.put('tempBt', var.get('intByte'))
            # for JS loop
            var.put('x', (var.get('thirdLength') - Js(1.0)))
            while (var.get('x') >= Js(0.0)):
                var.put('tempBt', var.get('dec')(var.get('tempBt'), var.get('thirdKeyBt').get(var.get('x'))))
                # update
                (var.put('x', Js(var.get('x').to_number()) - Js(1)) + Js(1))
            # for JS loop
            var.put('y', (var.get('secondLength') - Js(1.0)))
            while (var.get('y') >= Js(0.0)):
                var.put('tempBt', var.get('dec')(var.get('tempBt'), var.get('secondKeyBt').get(var.get('y'))))
                # update
                (var.put('y', Js(var.get('y').to_number()) - Js(1)) + Js(1))
            # for JS loop
            var.put('z', (var.get('firstLength') - Js(1.0)))
            while (var.get('z') >= Js(0.0)):
                var.put('tempBt', var.get('dec')(var.get('tempBt'), var.get('firstKeyBt').get(var.get('z'))))
                # update
                (var.put('z', Js(var.get('z').to_number()) - Js(1)) + Js(1))
            var.put('decByte', var.get('tempBt'))
        else:
            if ((((var.get('firstKey') != var.get(u"null")) and (var.get('firstKey') != Js(''))) and (
                    var.get('secondKey') != var.get(u"null"))) and (var.get('secondKey') != Js(''))):

                var.put('tempBt', var.get('intByte'))
                # for JS loop
                var.put('x', (var.get('secondLength') - Js(1.0)))
                while (var.get('x') >= Js(0.0)):
                    var.put('tempBt', var.get('dec')(var.get('tempBt'), var.get('secondKeyBt').get(var.get('x'))))
                    # update
                    (var.put('x', Js(var.get('x').to_number()) - Js(1)) + Js(1))
                # for JS loop
                var.put('y', (var.get('firstLength') - Js(1.0)))
                while (var.get('y') >= Js(0.0)):
                    var.put('tempBt', var.get('dec')(var.get('tempBt'), var.get('firstKeyBt').get(var.get('y'))))
                    # update
                    (var.put('y', Js(var.get('y').to_number()) - Js(1)) + Js(1))
                var.put('decByte', var.get('tempBt'))
            else:
                if ((var.get('firstKey') != var.get(u"null")) and (var.get('firstKey') != Js(''))):

                    var.put('tempBt', var.get('intByte'))
                    # for JS loop
                    var.put('x', (var.get('firstLength') - Js(1.0)))
                    while (var.get('x') >= Js(0.0)):
                        var.put('tempBt', var.get('dec')(var.get('tempBt'), var.get('firstKeyBt').get(var.get('x'))))
                        # update
                        (var.put('x', Js(var.get('x').to_number()) - Js(1)) + Js(1))
                    var.put('decByte', var.get('tempBt'))
        var.put('decStr', var.get('byteToString')(var.get('decByte')), '+')
        # update
        (var.put('i', Js(var.get('i').to_number()) + Js(1)) - Js(1))
    return var.get('decStr')


PyJsHoisted_strDec_.func_name = 'strDec'
var.put('strDec', PyJsHoisted_strDec_)


@Js
def PyJsHoisted_getKeyBytes_(key, this, arguments, var=var):
    var = Scope({'key': key, 'this': this, 'arguments': arguments}, var)
    var.registers(['iterator', 'leng', 'i', 'keyBytes', 'remainder', 'key'])
    var.put('keyBytes', var.get('Array').create())
    var.put('leng', var.get('key').get('length'))
    var.put('iterator', var.get('parseInt')((var.get('leng') / Js(4.0))))
    var.put('remainder', (var.get('leng') % Js(4.0)))
    var.put('i', Js(0.0))
    # for JS loop
    var.put('i', Js(0.0))
    while (var.get('i') < var.get('iterator')):
        var.get('keyBytes').put(var.get('i'), var.get('strToBt')(
            var.get('key').callprop('substring', ((var.get('i') * Js(4.0)) + Js(0.0)),
                                    ((var.get('i') * Js(4.0)) + Js(4.0)))))
        # update
        (var.put('i', Js(var.get('i').to_number()) + Js(1)) - Js(1))
    if (var.get('remainder') > Js(0.0)):
        var.get('keyBytes').put(var.get('i'), var.get('strToBt')(
            var.get('key').callprop('substring', ((var.get('i') * Js(4.0)) + Js(0.0)), var.get('leng'))))
    return var.get('keyBytes')


PyJsHoisted_getKeyBytes_.func_name = 'getKeyBytes'
var.put('getKeyBytes', PyJsHoisted_getKeyBytes_)


@Js
def PyJsHoisted_strToBt_(str, this, arguments, var=var):
    var = Scope({'str': str, 'this': this, 'arguments': arguments}, var)
    var.registers(['p', 'bt', 'j', 'leng', 'i', 'q', 'str', 'k', 'pow', 'm'])
    var.put('leng', var.get('str').get('length'))
    var.put('bt', var.get('Array').create(Js(64.0)))
    if (var.get('leng') < Js(4.0)):
        var.put('i', Js(0.0))
        var.put('j', Js(0.0))
        var.put('p', Js(0.0))
        var.put('q', Js(0.0))
        # for JS loop
        var.put('i', Js(0.0))
        while (var.get('i') < var.get('leng')):
            var.put('k', var.get('str').callprop('charCodeAt', var.get('i')))
            # for JS loop
            var.put('j', Js(0.0))
            while (var.get('j') < Js(16.0)):
                var.put('pow', Js(1.0))
                var.put('m', Js(0.0))
                # for JS loop
                var.put('m', Js(15.0))
                while (var.get('m') > var.get('j')):
                    var.put('pow', Js(2.0), '*')
                    # update
                    (var.put('m', Js(var.get('m').to_number()) - Js(1)) + Js(1))
                var.get('bt').put(((Js(16.0) * var.get('i')) + var.get('j')),
                                  (var.get('parseInt')((var.get('k') / var.get('pow'))) % Js(2.0)))
                # update
                (var.put('j', Js(var.get('j').to_number()) + Js(1)) - Js(1))
            # update
            (var.put('i', Js(var.get('i').to_number()) + Js(1)) - Js(1))
        # for JS loop
        var.put('p', var.get('leng'))
        while (var.get('p') < Js(4.0)):
            var.put('k', Js(0.0))
            # for JS loop
            var.put('q', Js(0.0))
            while (var.get('q') < Js(16.0)):
                var.put('pow', Js(1.0))
                var.put('m', Js(0.0))
                # for JS loop
                var.put('m', Js(15.0))
                while (var.get('m') > var.get('q')):
                    var.put('pow', Js(2.0), '*')
                    # update
                    (var.put('m', Js(var.get('m').to_number()) - Js(1)) + Js(1))
                var.get('bt').put(((Js(16.0) * var.get('p')) + var.get('q')),
                                  (var.get('parseInt')((var.get('k') / var.get('pow'))) % Js(2.0)))
                # update
                (var.put('q', Js(var.get('q').to_number()) + Js(1)) - Js(1))
            # update
            (var.put('p', Js(var.get('p').to_number()) + Js(1)) - Js(1))
    else:
        # for JS loop
        var.put('i', Js(0.0))
        while (var.get('i') < Js(4.0)):
            var.put('k', var.get('str').callprop('charCodeAt', var.get('i')))
            # for JS loop
            var.put('j', Js(0.0))
            while (var.get('j') < Js(16.0)):
                var.put('pow', Js(1.0))
                # for JS loop
                var.put('m', Js(15.0))
                while (var.get('m') > var.get('j')):
                    var.put('pow', Js(2.0), '*')
                    # update
                    (var.put('m', Js(var.get('m').to_number()) - Js(1)) + Js(1))
                var.get('bt').put(((Js(16.0) * var.get('i')) + var.get('j')),
                                  (var.get('parseInt')((var.get('k') / var.get('pow'))) % Js(2.0)))
                # update
                (var.put('j', Js(var.get('j').to_number()) + Js(1)) - Js(1))
            # update
            (var.put('i', Js(var.get('i').to_number()) + Js(1)) - Js(1))
    return var.get('bt')


PyJsHoisted_strToBt_.func_name = 'strToBt'
var.put('strToBt', PyJsHoisted_strToBt_)


@Js
def PyJsHoisted_bt4ToHex_(binary, this, arguments, var=var):
    var = Scope({'binary': binary, 'this': this, 'arguments': arguments}, var)
    var.registers(['hex', 'binary'])

    while 1:
        SWITCHED = False
        CONDITION = (var.get('binary'))
        if SWITCHED or PyJsStrictEq(CONDITION, Js('0000')):
            SWITCHED = True
            var.put('hex', Js('0'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('0001')):
            SWITCHED = True
            var.put('hex', Js('1'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('0010')):
            SWITCHED = True
            var.put('hex', Js('2'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('0011')):
            SWITCHED = True
            var.put('hex', Js('3'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('0100')):
            SWITCHED = True
            var.put('hex', Js('4'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('0101')):
            SWITCHED = True
            var.put('hex', Js('5'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('0110')):
            SWITCHED = True
            var.put('hex', Js('6'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('0111')):
            SWITCHED = True
            var.put('hex', Js('7'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('1000')):
            SWITCHED = True
            var.put('hex', Js('8'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('1001')):
            SWITCHED = True
            var.put('hex', Js('9'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('1010')):
            SWITCHED = True
            var.put('hex', Js('A'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('1011')):
            SWITCHED = True
            var.put('hex', Js('B'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('1100')):
            SWITCHED = True
            var.put('hex', Js('C'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('1101')):
            SWITCHED = True
            var.put('hex', Js('D'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('1110')):
            SWITCHED = True
            var.put('hex', Js('E'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('1111')):
            SWITCHED = True
            var.put('hex', Js('F'))
            break
        SWITCHED = True
        break
    return var.get('hex')


PyJsHoisted_bt4ToHex_.func_name = 'bt4ToHex'
var.put('bt4ToHex', PyJsHoisted_bt4ToHex_)


@Js
def PyJsHoisted_hexToBt4_(hex, this, arguments, var=var):
    var = Scope({'hex': hex, 'this': this, 'arguments': arguments}, var)
    var.registers(['hex', 'binary'])

    while 1:
        SWITCHED = False
        CONDITION = (var.get('hex'))
        if SWITCHED or PyJsStrictEq(CONDITION, Js('0')):
            SWITCHED = True
            var.put('binary', Js('0000'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('1')):
            SWITCHED = True
            var.put('binary', Js('0001'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('2')):
            SWITCHED = True
            var.put('binary', Js('0010'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('3')):
            SWITCHED = True
            var.put('binary', Js('0011'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('4')):
            SWITCHED = True
            var.put('binary', Js('0100'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('5')):
            SWITCHED = True
            var.put('binary', Js('0101'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('6')):
            SWITCHED = True
            var.put('binary', Js('0110'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('7')):
            SWITCHED = True
            var.put('binary', Js('0111'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('8')):
            SWITCHED = True
            var.put('binary', Js('1000'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('9')):
            SWITCHED = True
            var.put('binary', Js('1001'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('A')):
            SWITCHED = True
            var.put('binary', Js('1010'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('B')):
            SWITCHED = True
            var.put('binary', Js('1011'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('C')):
            SWITCHED = True
            var.put('binary', Js('1100'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('D')):
            SWITCHED = True
            var.put('binary', Js('1101'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('E')):
            SWITCHED = True
            var.put('binary', Js('1110'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js('F')):
            SWITCHED = True
            var.put('binary', Js('1111'))
            break
        SWITCHED = True
        break
    return var.get('binary')


PyJsHoisted_hexToBt4_.func_name = 'hexToBt4'
var.put('hexToBt4', PyJsHoisted_hexToBt4_)


@Js
def PyJsHoisted_byteToString_(byteData, this, arguments, var=var):
    var = Scope({'byteData': byteData, 'this': this, 'arguments': arguments}, var)
    var.registers(['byteData', 'pow', 'count', 'str'])
    var.put('str', Js(''))
    # for JS loop
    var.put('i', Js(0.0))
    while (var.get('i') < Js(4.0)):
        var.put('count', Js(0.0))
        # for JS loop
        var.put('j', Js(0.0))
        while (var.get('j') < Js(16.0)):
            var.put('pow', Js(1.0))
            # for JS loop
            var.put('m', Js(15.0))
            while (var.get('m') > var.get('j')):
                var.put('pow', Js(2.0), '*')
                # update
                (var.put('m', Js(var.get('m').to_number()) - Js(1)) + Js(1))
            var.put('count', (var.get('byteData').get(((Js(16.0) * var.get('i')) + var.get('j'))) * var.get('pow')),
                    '+')
            # update
            (var.put('j', Js(var.get('j').to_number()) + Js(1)) - Js(1))
        if (var.get('count') != Js(0.0)):
            var.put('str', var.get('String').callprop('fromCharCode', var.get('count')), '+')
        # update
        (var.put('i', Js(var.get('i').to_number()) + Js(1)) - Js(1))
    return var.get('str')


PyJsHoisted_byteToString_.func_name = 'byteToString'
var.put('byteToString', PyJsHoisted_byteToString_)


@Js
def PyJsHoisted_bt64ToHex_(byteData, this, arguments, var=var):
    var = Scope({'byteData': byteData, 'this': this, 'arguments': arguments}, var)
    var.registers(['byteData', 'hex', 'bt'])
    var.put('hex', Js(''))
    # for JS loop
    var.put('i', Js(0.0))
    while (var.get('i') < Js(16.0)):
        var.put('bt', Js(''))
        # for JS loop
        var.put('j', Js(0.0))
        while (var.get('j') < Js(4.0)):
            var.put('bt', var.get('byteData').get(((var.get('i') * Js(4.0)) + var.get('j'))), '+')
            # update
            (var.put('j', Js(var.get('j').to_number()) + Js(1)) - Js(1))
        var.put('hex', var.get('bt4ToHex')(var.get('bt')), '+')
        # update
        (var.put('i', Js(var.get('i').to_number()) + Js(1)) - Js(1))
    return var.get('hex')


PyJsHoisted_bt64ToHex_.func_name = 'bt64ToHex'
var.put('bt64ToHex', PyJsHoisted_bt64ToHex_)


@Js
def PyJsHoisted_hexToBt64_(hex, this, arguments, var=var):
    var = Scope({'hex': hex, 'this': this, 'arguments': arguments}, var)
    var.registers(['hex', 'binary'])
    var.put('binary', Js(''))
    # for JS loop
    var.put('i', Js(0.0))
    while (var.get('i') < Js(16.0)):
        var.put('binary',
                var.get('hexToBt4')(var.get('hex').callprop('substring', var.get('i'), (var.get('i') + Js(1.0)))), '+')
        # update
        (var.put('i', Js(var.get('i').to_number()) + Js(1)) - Js(1))
    return var.get('binary')


PyJsHoisted_hexToBt64_.func_name = 'hexToBt64'
var.put('hexToBt64', PyJsHoisted_hexToBt64_)


@Js
def PyJsHoisted_enc_(dataByte, keyByte, this, arguments, var=var):
    var = Scope({'dataByte': dataByte, 'keyByte': keyByte, 'this': this, 'arguments': arguments}, var)
    var.registers(
        ['ipRight', 'j', 'i', 'keyByte', 'n', 'tempRight', 'dataByte', 'ipLeft', 'k', 'keys', 'tempLeft', 'finalData',
         'ipByte', 'm', 'key'])
    var.put('keys', var.get('generateKeys')(var.get('keyByte')))
    var.put('ipByte', var.get('initPermute')(var.get('dataByte')))
    var.put('ipLeft', var.get('Array').create(Js(32.0)))
    var.put('ipRight', var.get('Array').create(Js(32.0)))
    var.put('tempLeft', var.get('Array').create(Js(32.0)))
    var.put('i', Js(0.0))
    var.put('j', Js(0.0))
    var.put('k', Js(0.0))
    var.put('m', Js(0.0))
    var.put('n', Js(0.0))
    # for JS loop
    var.put('k', Js(0.0))
    while (var.get('k') < Js(32.0)):
        var.get('ipLeft').put(var.get('k'), var.get('ipByte').get(var.get('k')))
        var.get('ipRight').put(var.get('k'), var.get('ipByte').get((Js(32.0) + var.get('k'))))
        # update
        (var.put('k', Js(var.get('k').to_number()) + Js(1)) - Js(1))
    # for JS loop
    var.put('i', Js(0.0))
    while (var.get('i') < Js(16.0)):
        # for JS loop
        var.put('j', Js(0.0))
        while (var.get('j') < Js(32.0)):
            var.get('tempLeft').put(var.get('j'), var.get('ipLeft').get(var.get('j')))
            var.get('ipLeft').put(var.get('j'), var.get('ipRight').get(var.get('j')))
            # update
            (var.put('j', Js(var.get('j').to_number()) + Js(1)) - Js(1))
        var.put('key', var.get('Array').create(Js(48.0)))
        # for JS loop
        var.put('m', Js(0.0))
        while (var.get('m') < Js(48.0)):
            var.get('key').put(var.get('m'), var.get('keys').get(var.get('i')).get(var.get('m')))
            # update
            (var.put('m', Js(var.get('m').to_number()) + Js(1)) - Js(1))
        var.put('tempRight', var.get('xor')(var.get('pPermute')(
            var.get('sBoxPermute')(var.get('xor')(var.get('expandPermute')(var.get('ipRight')), var.get('key')))),
            var.get('tempLeft')))
        # for JS loop
        var.put('n', Js(0.0))
        while (var.get('n') < Js(32.0)):
            var.get('ipRight').put(var.get('n'), var.get('tempRight').get(var.get('n')))
            # update
            (var.put('n', Js(var.get('n').to_number()) + Js(1)) - Js(1))
        # update
        (var.put('i', Js(var.get('i').to_number()) + Js(1)) - Js(1))
    var.put('finalData', var.get('Array').create(Js(64.0)))
    # for JS loop
    var.put('i', Js(0.0))
    while (var.get('i') < Js(32.0)):
        var.get('finalData').put(var.get('i'), var.get('ipRight').get(var.get('i')))
        var.get('finalData').put((Js(32.0) + var.get('i')), var.get('ipLeft').get(var.get('i')))
        # update
        (var.put('i', Js(var.get('i').to_number()) + Js(1)) - Js(1))
    return var.get('finallyPermute')(var.get('finalData'))


PyJsHoisted_enc_.func_name = 'enc'
var.put('enc', PyJsHoisted_enc_)


@Js
def PyJsHoisted_dec_(dataByte, keyByte, this, arguments, var=var):
    var = Scope({'dataByte': dataByte, 'keyByte': keyByte, 'this': this, 'arguments': arguments}, var)
    var.registers(
        ['ipRight', 'j', 'i', 'keyByte', 'n', 'tempRight', 'dataByte', 'ipLeft', 'k', 'keys', 'tempLeft', 'finalData',
         'ipByte', 'm', 'key'])
    var.put('keys', var.get('generateKeys')(var.get('keyByte')))
    var.put('ipByte', var.get('initPermute')(var.get('dataByte')))
    var.put('ipLeft', var.get('Array').create(Js(32.0)))
    var.put('ipRight', var.get('Array').create(Js(32.0)))
    var.put('tempLeft', var.get('Array').create(Js(32.0)))
    var.put('i', Js(0.0))
    var.put('j', Js(0.0))
    var.put('k', Js(0.0))
    var.put('m', Js(0.0))
    var.put('n', Js(0.0))
    # for JS loop
    var.put('k', Js(0.0))
    while (var.get('k') < Js(32.0)):
        var.get('ipLeft').put(var.get('k'), var.get('ipByte').get(var.get('k')))
        var.get('ipRight').put(var.get('k'), var.get('ipByte').get((Js(32.0) + var.get('k'))))
        # update
        (var.put('k', Js(var.get('k').to_number()) + Js(1)) - Js(1))
    # for JS loop
    var.put('i', Js(15.0))
    while (var.get('i') >= Js(0.0)):
        # for JS loop
        var.put('j', Js(0.0))
        while (var.get('j') < Js(32.0)):
            var.get('tempLeft').put(var.get('j'), var.get('ipLeft').get(var.get('j')))
            var.get('ipLeft').put(var.get('j'), var.get('ipRight').get(var.get('j')))
            # update
            (var.put('j', Js(var.get('j').to_number()) + Js(1)) - Js(1))
        var.put('key', var.get('Array').create(Js(48.0)))
        # for JS loop
        var.put('m', Js(0.0))
        while (var.get('m') < Js(48.0)):
            var.get('key').put(var.get('m'), var.get('keys').get(var.get('i')).get(var.get('m')))
            # update
            (var.put('m', Js(var.get('m').to_number()) + Js(1)) - Js(1))
        var.put('tempRight', var.get('xor')(var.get('pPermute')(
            var.get('sBoxPermute')(var.get('xor')(var.get('expandPermute')(var.get('ipRight')), var.get('key')))),
            var.get('tempLeft')))
        # for JS loop
        var.put('n', Js(0.0))
        while (var.get('n') < Js(32.0)):
            var.get('ipRight').put(var.get('n'), var.get('tempRight').get(var.get('n')))
            # update
            (var.put('n', Js(var.get('n').to_number()) + Js(1)) - Js(1))
        # update
        (var.put('i', Js(var.get('i').to_number()) - Js(1)) + Js(1))
    var.put('finalData', var.get('Array').create(Js(64.0)))
    # for JS loop
    var.put('i', Js(0.0))
    while (var.get('i') < Js(32.0)):
        var.get('finalData').put(var.get('i'), var.get('ipRight').get(var.get('i')))
        var.get('finalData').put((Js(32.0) + var.get('i')), var.get('ipLeft').get(var.get('i')))
        # update
        (var.put('i', Js(var.get('i').to_number()) + Js(1)) - Js(1))
    return var.get('finallyPermute')(var.get('finalData'))


PyJsHoisted_dec_.func_name = 'dec'
var.put('dec', PyJsHoisted_dec_)


@Js
def PyJsHoisted_initPermute_(originalData, this, arguments, var=var):
    var = Scope({'originalData': originalData, 'this': this, 'arguments': arguments}, var)
    var.registers(['ipByte', 'originalData'])
    var.put('ipByte', var.get('Array').create(Js(64.0)))
    # for JS loop
    PyJsComma(PyJsComma(var.put('i', Js(0.0)), var.put('m', Js(1.0))), var.put('n', Js(0.0)))
    while (var.get('i') < Js(4.0)):
        # for JS loop
        PyJsComma(var.put('j', Js(7.0)), var.put('k', Js(0.0)))
        while (var.get('j') >= Js(0.0)):
            var.get('ipByte').put(((var.get('i') * Js(8.0)) + var.get('k')),
                                  var.get('originalData').get(((var.get('j') * Js(8.0)) + var.get('m'))))
            var.get('ipByte').put((((var.get('i') * Js(8.0)) + var.get('k')) + Js(32.0)),
                                  var.get('originalData').get(((var.get('j') * Js(8.0)) + var.get('n'))))
            # update
            PyJsComma((var.put('j', Js(var.get('j').to_number()) - Js(1)) + Js(1)),
                      (var.put('k', Js(var.get('k').to_number()) + Js(1)) - Js(1)))
        # update
        PyJsComma(PyJsComma((var.put('i', Js(var.get('i').to_number()) + Js(1)) - Js(1)), var.put('m', Js(2.0), '+')),
                  var.put('n', Js(2.0), '+'))
    return var.get('ipByte')


PyJsHoisted_initPermute_.func_name = 'initPermute'
var.put('initPermute', PyJsHoisted_initPermute_)


@Js
def PyJsHoisted_expandPermute_(rightData, this, arguments, var=var):
    var = Scope({'rightData': rightData, 'this': this, 'arguments': arguments}, var)
    var.registers(['rightData', 'epByte'])
    var.put('epByte', var.get('Array').create(Js(48.0)))
    # for JS loop
    var.put('i', Js(0.0))
    while (var.get('i') < Js(8.0)):
        if (var.get('i') == Js(0.0)):
            var.get('epByte').put(((var.get('i') * Js(6.0)) + Js(0.0)), var.get('rightData').get('31'))
        else:
            var.get('epByte').put(((var.get('i') * Js(6.0)) + Js(0.0)),
                                  var.get('rightData').get(((var.get('i') * Js(4.0)) - Js(1.0))))
        var.get('epByte').put(((var.get('i') * Js(6.0)) + Js(1.0)),
                              var.get('rightData').get(((var.get('i') * Js(4.0)) + Js(0.0))))
        var.get('epByte').put(((var.get('i') * Js(6.0)) + Js(2.0)),
                              var.get('rightData').get(((var.get('i') * Js(4.0)) + Js(1.0))))
        var.get('epByte').put(((var.get('i') * Js(6.0)) + Js(3.0)),
                              var.get('rightData').get(((var.get('i') * Js(4.0)) + Js(2.0))))
        var.get('epByte').put(((var.get('i') * Js(6.0)) + Js(4.0)),
                              var.get('rightData').get(((var.get('i') * Js(4.0)) + Js(3.0))))
        if (var.get('i') == Js(7.0)):
            var.get('epByte').put(((var.get('i') * Js(6.0)) + Js(5.0)), var.get('rightData').get('0'))
        else:
            var.get('epByte').put(((var.get('i') * Js(6.0)) + Js(5.0)),
                                  var.get('rightData').get(((var.get('i') * Js(4.0)) + Js(4.0))))
        # update
        (var.put('i', Js(var.get('i').to_number()) + Js(1)) - Js(1))
    return var.get('epByte')


PyJsHoisted_expandPermute_.func_name = 'expandPermute'
var.put('expandPermute', PyJsHoisted_expandPermute_)


@Js
def PyJsHoisted_xor_(byteOne, byteTwo, this, arguments, var=var):
    var = Scope({'byteOne': byteOne, 'byteTwo': byteTwo, 'this': this, 'arguments': arguments}, var)
    var.registers(['xorByte', 'byteOne', 'byteTwo'])
    var.put('xorByte', var.get('Array').create(var.get('byteOne').get('length')))
    # for JS loop
    var.put('i', Js(0.0))
    while (var.get('i') < var.get('byteOne').get('length')):
        var.get('xorByte').put(var.get('i'),
                               (var.get('byteOne').get(var.get('i')) ^ var.get('byteTwo').get(var.get('i'))))
        # update
        (var.put('i', Js(var.get('i').to_number()) + Js(1)) - Js(1))
    return var.get('xorByte')


PyJsHoisted_xor_.func_name = 'xor'
var.put('xor', PyJsHoisted_xor_)


@Js
def PyJsHoisted_sBoxPermute_(expandByte, this, arguments, var=var):
    var = Scope({'expandByte': expandByte, 'this': this, 'arguments': arguments}, var)
    var.registers(['s3', 's6', 'j', 'i', 's4', 'sBoxByte', 's1', 's5', 'expandByte', 's2', 'binary', 's8', 's7'])
    var.put('sBoxByte', var.get('Array').create(Js(32.0)))
    var.put('binary', Js(''))
    var.put('s1', Js([Js([Js(14.0), Js(4.0), Js(13.0), Js(1.0), Js(2.0), Js(15.0), Js(11.0), Js(8.0), Js(3.0), Js(10.0),
                          Js(6.0), Js(12.0), Js(5.0), Js(9.0), Js(0.0), Js(7.0)]),
                      Js([Js(0.0), Js(15.0), Js(7.0), Js(4.0), Js(14.0), Js(2.0), Js(13.0), Js(1.0), Js(10.0), Js(6.0),
                          Js(12.0), Js(11.0), Js(9.0), Js(5.0), Js(3.0), Js(8.0)]),
                      Js([Js(4.0), Js(1.0), Js(14.0), Js(8.0), Js(13.0), Js(6.0), Js(2.0), Js(11.0), Js(15.0), Js(12.0),
                          Js(9.0), Js(7.0), Js(3.0), Js(10.0), Js(5.0), Js(0.0)]),
                      Js([Js(15.0), Js(12.0), Js(8.0), Js(2.0), Js(4.0), Js(9.0), Js(1.0), Js(7.0), Js(5.0), Js(11.0),
                          Js(3.0), Js(14.0), Js(10.0), Js(0.0), Js(6.0), Js(13.0)])]))
    var.put('s2', Js([Js([Js(15.0), Js(1.0), Js(8.0), Js(14.0), Js(6.0), Js(11.0), Js(3.0), Js(4.0), Js(9.0), Js(7.0),
                          Js(2.0), Js(13.0), Js(12.0), Js(0.0), Js(5.0), Js(10.0)]),
                      Js([Js(3.0), Js(13.0), Js(4.0), Js(7.0), Js(15.0), Js(2.0), Js(8.0), Js(14.0), Js(12.0), Js(0.0),
                          Js(1.0), Js(10.0), Js(6.0), Js(9.0), Js(11.0), Js(5.0)]),
                      Js([Js(0.0), Js(14.0), Js(7.0), Js(11.0), Js(10.0), Js(4.0), Js(13.0), Js(1.0), Js(5.0), Js(8.0),
                          Js(12.0), Js(6.0), Js(9.0), Js(3.0), Js(2.0), Js(15.0)]),
                      Js([Js(13.0), Js(8.0), Js(10.0), Js(1.0), Js(3.0), Js(15.0), Js(4.0), Js(2.0), Js(11.0), Js(6.0),
                          Js(7.0), Js(12.0), Js(0.0), Js(5.0), Js(14.0), Js(9.0)])]))
    var.put('s3', Js([Js([Js(10.0), Js(0.0), Js(9.0), Js(14.0), Js(6.0), Js(3.0), Js(15.0), Js(5.0), Js(1.0), Js(13.0),
                          Js(12.0), Js(7.0), Js(11.0), Js(4.0), Js(2.0), Js(8.0)]),
                      Js([Js(13.0), Js(7.0), Js(0.0), Js(9.0), Js(3.0), Js(4.0), Js(6.0), Js(10.0), Js(2.0), Js(8.0),
                          Js(5.0), Js(14.0), Js(12.0), Js(11.0), Js(15.0), Js(1.0)]),
                      Js([Js(13.0), Js(6.0), Js(4.0), Js(9.0), Js(8.0), Js(15.0), Js(3.0), Js(0.0), Js(11.0), Js(1.0),
                          Js(2.0), Js(12.0), Js(5.0), Js(10.0), Js(14.0), Js(7.0)]),
                      Js([Js(1.0), Js(10.0), Js(13.0), Js(0.0), Js(6.0), Js(9.0), Js(8.0), Js(7.0), Js(4.0), Js(15.0),
                          Js(14.0), Js(3.0), Js(11.0), Js(5.0), Js(2.0), Js(12.0)])]))
    var.put('s4', Js([Js([Js(7.0), Js(13.0), Js(14.0), Js(3.0), Js(0.0), Js(6.0), Js(9.0), Js(10.0), Js(1.0), Js(2.0),
                          Js(8.0), Js(5.0), Js(11.0), Js(12.0), Js(4.0), Js(15.0)]),
                      Js([Js(13.0), Js(8.0), Js(11.0), Js(5.0), Js(6.0), Js(15.0), Js(0.0), Js(3.0), Js(4.0), Js(7.0),
                          Js(2.0), Js(12.0), Js(1.0), Js(10.0), Js(14.0), Js(9.0)]),
                      Js([Js(10.0), Js(6.0), Js(9.0), Js(0.0), Js(12.0), Js(11.0), Js(7.0), Js(13.0), Js(15.0), Js(1.0),
                          Js(3.0), Js(14.0), Js(5.0), Js(2.0), Js(8.0), Js(4.0)]),
                      Js([Js(3.0), Js(15.0), Js(0.0), Js(6.0), Js(10.0), Js(1.0), Js(13.0), Js(8.0), Js(9.0), Js(4.0),
                          Js(5.0), Js(11.0), Js(12.0), Js(7.0), Js(2.0), Js(14.0)])]))
    var.put('s5', Js([Js([Js(2.0), Js(12.0), Js(4.0), Js(1.0), Js(7.0), Js(10.0), Js(11.0), Js(6.0), Js(8.0), Js(5.0),
                          Js(3.0), Js(15.0), Js(13.0), Js(0.0), Js(14.0), Js(9.0)]),
                      Js([Js(14.0), Js(11.0), Js(2.0), Js(12.0), Js(4.0), Js(7.0), Js(13.0), Js(1.0), Js(5.0), Js(0.0),
                          Js(15.0), Js(10.0), Js(3.0), Js(9.0), Js(8.0), Js(6.0)]),
                      Js([Js(4.0), Js(2.0), Js(1.0), Js(11.0), Js(10.0), Js(13.0), Js(7.0), Js(8.0), Js(15.0), Js(9.0),
                          Js(12.0), Js(5.0), Js(6.0), Js(3.0), Js(0.0), Js(14.0)]),
                      Js([Js(11.0), Js(8.0), Js(12.0), Js(7.0), Js(1.0), Js(14.0), Js(2.0), Js(13.0), Js(6.0), Js(15.0),
                          Js(0.0), Js(9.0), Js(10.0), Js(4.0), Js(5.0), Js(3.0)])]))
    var.put('s6', Js([Js([Js(12.0), Js(1.0), Js(10.0), Js(15.0), Js(9.0), Js(2.0), Js(6.0), Js(8.0), Js(0.0), Js(13.0),
                          Js(3.0), Js(4.0), Js(14.0), Js(7.0), Js(5.0), Js(11.0)]),
                      Js([Js(10.0), Js(15.0), Js(4.0), Js(2.0), Js(7.0), Js(12.0), Js(9.0), Js(5.0), Js(6.0), Js(1.0),
                          Js(13.0), Js(14.0), Js(0.0), Js(11.0), Js(3.0), Js(8.0)]),
                      Js([Js(9.0), Js(14.0), Js(15.0), Js(5.0), Js(2.0), Js(8.0), Js(12.0), Js(3.0), Js(7.0), Js(0.0),
                          Js(4.0), Js(10.0), Js(1.0), Js(13.0), Js(11.0), Js(6.0)]),
                      Js([Js(4.0), Js(3.0), Js(2.0), Js(12.0), Js(9.0), Js(5.0), Js(15.0), Js(10.0), Js(11.0), Js(14.0),
                          Js(1.0), Js(7.0), Js(6.0), Js(0.0), Js(8.0), Js(13.0)])]))
    var.put('s7', Js([Js([Js(4.0), Js(11.0), Js(2.0), Js(14.0), Js(15.0), Js(0.0), Js(8.0), Js(13.0), Js(3.0), Js(12.0),
                          Js(9.0), Js(7.0), Js(5.0), Js(10.0), Js(6.0), Js(1.0)]),
                      Js([Js(13.0), Js(0.0), Js(11.0), Js(7.0), Js(4.0), Js(9.0), Js(1.0), Js(10.0), Js(14.0), Js(3.0),
                          Js(5.0), Js(12.0), Js(2.0), Js(15.0), Js(8.0), Js(6.0)]),
                      Js([Js(1.0), Js(4.0), Js(11.0), Js(13.0), Js(12.0), Js(3.0), Js(7.0), Js(14.0), Js(10.0),
                          Js(15.0), Js(6.0), Js(8.0), Js(0.0), Js(5.0), Js(9.0), Js(2.0)]),
                      Js([Js(6.0), Js(11.0), Js(13.0), Js(8.0), Js(1.0), Js(4.0), Js(10.0), Js(7.0), Js(9.0), Js(5.0),
                          Js(0.0), Js(15.0), Js(14.0), Js(2.0), Js(3.0), Js(12.0)])]))
    var.put('s8', Js([Js([Js(13.0), Js(2.0), Js(8.0), Js(4.0), Js(6.0), Js(15.0), Js(11.0), Js(1.0), Js(10.0), Js(9.0),
                          Js(3.0), Js(14.0), Js(5.0), Js(0.0), Js(12.0), Js(7.0)]),
                      Js([Js(1.0), Js(15.0), Js(13.0), Js(8.0), Js(10.0), Js(3.0), Js(7.0), Js(4.0), Js(12.0), Js(5.0),
                          Js(6.0), Js(11.0), Js(0.0), Js(14.0), Js(9.0), Js(2.0)]),
                      Js([Js(7.0), Js(11.0), Js(4.0), Js(1.0), Js(9.0), Js(12.0), Js(14.0), Js(2.0), Js(0.0), Js(6.0),
                          Js(10.0), Js(13.0), Js(15.0), Js(3.0), Js(5.0), Js(8.0)]),
                      Js([Js(2.0), Js(1.0), Js(14.0), Js(7.0), Js(4.0), Js(10.0), Js(8.0), Js(13.0), Js(15.0), Js(12.0),
                          Js(9.0), Js(0.0), Js(3.0), Js(5.0), Js(6.0), Js(11.0)])]))
    # for JS loop
    var.put('m', Js(0.0))
    while (var.get('m') < Js(8.0)):
        var.put('i', Js(0.0))
        var.put('j', Js(0.0))
        var.put('i', ((var.get('expandByte').get(((var.get('m') * Js(6.0)) + Js(0.0))) * Js(2.0)) + var.get(
            'expandByte').get(((var.get('m') * Js(6.0)) + Js(5.0)))))
        var.put('j', ((((((var.get('expandByte').get(((var.get('m') * Js(6.0)) + Js(1.0))) * Js(2.0)) * Js(2.0)) * Js(
            2.0)) + ((var.get('expandByte').get(((var.get('m') * Js(6.0)) + Js(2.0))) * Js(2.0)) * Js(2.0))) + (
                               var.get('expandByte').get(((var.get('m') * Js(6.0)) + Js(3.0))) * Js(
                           2.0))) + var.get('expandByte').get(((var.get('m') * Js(6.0)) + Js(4.0)))))
        while 1:
            SWITCHED = False
            CONDITION = (var.get('m'))
            if SWITCHED or PyJsStrictEq(CONDITION, Js(0.0)):
                SWITCHED = True
                var.put('binary', var.get('getBoxBinary')(var.get('s1').get(var.get('i')).get(var.get('j'))))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(1.0)):
                SWITCHED = True
                var.put('binary', var.get('getBoxBinary')(var.get('s2').get(var.get('i')).get(var.get('j'))))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(2.0)):
                SWITCHED = True
                var.put('binary', var.get('getBoxBinary')(var.get('s3').get(var.get('i')).get(var.get('j'))))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(3.0)):
                SWITCHED = True
                var.put('binary', var.get('getBoxBinary')(var.get('s4').get(var.get('i')).get(var.get('j'))))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(4.0)):
                SWITCHED = True
                var.put('binary', var.get('getBoxBinary')(var.get('s5').get(var.get('i')).get(var.get('j'))))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(5.0)):
                SWITCHED = True
                var.put('binary', var.get('getBoxBinary')(var.get('s6').get(var.get('i')).get(var.get('j'))))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(6.0)):
                SWITCHED = True
                var.put('binary', var.get('getBoxBinary')(var.get('s7').get(var.get('i')).get(var.get('j'))))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(7.0)):
                SWITCHED = True
                var.put('binary', var.get('getBoxBinary')(var.get('s8').get(var.get('i')).get(var.get('j'))))
                break
            SWITCHED = True
            break
        var.get('sBoxByte').put(((var.get('m') * Js(4.0)) + Js(0.0)),
                                var.get('parseInt')(var.get('binary').callprop('substring', Js(0.0), Js(1.0))))
        var.get('sBoxByte').put(((var.get('m') * Js(4.0)) + Js(1.0)),
                                var.get('parseInt')(var.get('binary').callprop('substring', Js(1.0), Js(2.0))))
        var.get('sBoxByte').put(((var.get('m') * Js(4.0)) + Js(2.0)),
                                var.get('parseInt')(var.get('binary').callprop('substring', Js(2.0), Js(3.0))))
        var.get('sBoxByte').put(((var.get('m') * Js(4.0)) + Js(3.0)),
                                var.get('parseInt')(var.get('binary').callprop('substring', Js(3.0), Js(4.0))))
        # update
        (var.put('m', Js(var.get('m').to_number()) + Js(1)) - Js(1))
    return var.get('sBoxByte')


PyJsHoisted_sBoxPermute_.func_name = 'sBoxPermute'
var.put('sBoxPermute', PyJsHoisted_sBoxPermute_)


@Js
def PyJsHoisted_pPermute_(sBoxByte, this, arguments, var=var):
    var = Scope({'sBoxByte': sBoxByte, 'this': this, 'arguments': arguments}, var)
    var.registers(['pBoxPermute', 'sBoxByte'])
    var.put('pBoxPermute', var.get('Array').create(Js(32.0)))
    var.get('pBoxPermute').put('0', var.get('sBoxByte').get('15'))
    var.get('pBoxPermute').put('1', var.get('sBoxByte').get('6'))
    var.get('pBoxPermute').put('2', var.get('sBoxByte').get('19'))
    var.get('pBoxPermute').put('3', var.get('sBoxByte').get('20'))
    var.get('pBoxPermute').put('4', var.get('sBoxByte').get('28'))
    var.get('pBoxPermute').put('5', var.get('sBoxByte').get('11'))
    var.get('pBoxPermute').put('6', var.get('sBoxByte').get('27'))
    var.get('pBoxPermute').put('7', var.get('sBoxByte').get('16'))
    var.get('pBoxPermute').put('8', var.get('sBoxByte').get('0'))
    var.get('pBoxPermute').put('9', var.get('sBoxByte').get('14'))
    var.get('pBoxPermute').put('10', var.get('sBoxByte').get('22'))
    var.get('pBoxPermute').put('11', var.get('sBoxByte').get('25'))
    var.get('pBoxPermute').put('12', var.get('sBoxByte').get('4'))
    var.get('pBoxPermute').put('13', var.get('sBoxByte').get('17'))
    var.get('pBoxPermute').put('14', var.get('sBoxByte').get('30'))
    var.get('pBoxPermute').put('15', var.get('sBoxByte').get('9'))
    var.get('pBoxPermute').put('16', var.get('sBoxByte').get('1'))
    var.get('pBoxPermute').put('17', var.get('sBoxByte').get('7'))
    var.get('pBoxPermute').put('18', var.get('sBoxByte').get('23'))
    var.get('pBoxPermute').put('19', var.get('sBoxByte').get('13'))
    var.get('pBoxPermute').put('20', var.get('sBoxByte').get('31'))
    var.get('pBoxPermute').put('21', var.get('sBoxByte').get('26'))
    var.get('pBoxPermute').put('22', var.get('sBoxByte').get('2'))
    var.get('pBoxPermute').put('23', var.get('sBoxByte').get('8'))
    var.get('pBoxPermute').put('24', var.get('sBoxByte').get('18'))
    var.get('pBoxPermute').put('25', var.get('sBoxByte').get('12'))
    var.get('pBoxPermute').put('26', var.get('sBoxByte').get('29'))
    var.get('pBoxPermute').put('27', var.get('sBoxByte').get('5'))
    var.get('pBoxPermute').put('28', var.get('sBoxByte').get('21'))
    var.get('pBoxPermute').put('29', var.get('sBoxByte').get('10'))
    var.get('pBoxPermute').put('30', var.get('sBoxByte').get('3'))
    var.get('pBoxPermute').put('31', var.get('sBoxByte').get('24'))
    return var.get('pBoxPermute')


PyJsHoisted_pPermute_.func_name = 'pPermute'
var.put('pPermute', PyJsHoisted_pPermute_)


@Js
def PyJsHoisted_finallyPermute_(endByte, this, arguments, var=var):
    var = Scope({'endByte': endByte, 'this': this, 'arguments': arguments}, var)
    var.registers(['fpByte', 'endByte'])
    var.put('fpByte', var.get('Array').create(Js(64.0)))
    var.get('fpByte').put('0', var.get('endByte').get('39'))
    var.get('fpByte').put('1', var.get('endByte').get('7'))
    var.get('fpByte').put('2', var.get('endByte').get('47'))
    var.get('fpByte').put('3', var.get('endByte').get('15'))
    var.get('fpByte').put('4', var.get('endByte').get('55'))
    var.get('fpByte').put('5', var.get('endByte').get('23'))
    var.get('fpByte').put('6', var.get('endByte').get('63'))
    var.get('fpByte').put('7', var.get('endByte').get('31'))
    var.get('fpByte').put('8', var.get('endByte').get('38'))
    var.get('fpByte').put('9', var.get('endByte').get('6'))
    var.get('fpByte').put('10', var.get('endByte').get('46'))
    var.get('fpByte').put('11', var.get('endByte').get('14'))
    var.get('fpByte').put('12', var.get('endByte').get('54'))
    var.get('fpByte').put('13', var.get('endByte').get('22'))
    var.get('fpByte').put('14', var.get('endByte').get('62'))
    var.get('fpByte').put('15', var.get('endByte').get('30'))
    var.get('fpByte').put('16', var.get('endByte').get('37'))
    var.get('fpByte').put('17', var.get('endByte').get('5'))
    var.get('fpByte').put('18', var.get('endByte').get('45'))
    var.get('fpByte').put('19', var.get('endByte').get('13'))
    var.get('fpByte').put('20', var.get('endByte').get('53'))
    var.get('fpByte').put('21', var.get('endByte').get('21'))
    var.get('fpByte').put('22', var.get('endByte').get('61'))
    var.get('fpByte').put('23', var.get('endByte').get('29'))
    var.get('fpByte').put('24', var.get('endByte').get('36'))
    var.get('fpByte').put('25', var.get('endByte').get('4'))
    var.get('fpByte').put('26', var.get('endByte').get('44'))
    var.get('fpByte').put('27', var.get('endByte').get('12'))
    var.get('fpByte').put('28', var.get('endByte').get('52'))
    var.get('fpByte').put('29', var.get('endByte').get('20'))
    var.get('fpByte').put('30', var.get('endByte').get('60'))
    var.get('fpByte').put('31', var.get('endByte').get('28'))
    var.get('fpByte').put('32', var.get('endByte').get('35'))
    var.get('fpByte').put('33', var.get('endByte').get('3'))
    var.get('fpByte').put('34', var.get('endByte').get('43'))
    var.get('fpByte').put('35', var.get('endByte').get('11'))
    var.get('fpByte').put('36', var.get('endByte').get('51'))
    var.get('fpByte').put('37', var.get('endByte').get('19'))
    var.get('fpByte').put('38', var.get('endByte').get('59'))
    var.get('fpByte').put('39', var.get('endByte').get('27'))
    var.get('fpByte').put('40', var.get('endByte').get('34'))
    var.get('fpByte').put('41', var.get('endByte').get('2'))
    var.get('fpByte').put('42', var.get('endByte').get('42'))
    var.get('fpByte').put('43', var.get('endByte').get('10'))
    var.get('fpByte').put('44', var.get('endByte').get('50'))
    var.get('fpByte').put('45', var.get('endByte').get('18'))
    var.get('fpByte').put('46', var.get('endByte').get('58'))
    var.get('fpByte').put('47', var.get('endByte').get('26'))
    var.get('fpByte').put('48', var.get('endByte').get('33'))
    var.get('fpByte').put('49', var.get('endByte').get('1'))
    var.get('fpByte').put('50', var.get('endByte').get('41'))
    var.get('fpByte').put('51', var.get('endByte').get('9'))
    var.get('fpByte').put('52', var.get('endByte').get('49'))
    var.get('fpByte').put('53', var.get('endByte').get('17'))
    var.get('fpByte').put('54', var.get('endByte').get('57'))
    var.get('fpByte').put('55', var.get('endByte').get('25'))
    var.get('fpByte').put('56', var.get('endByte').get('32'))
    var.get('fpByte').put('57', var.get('endByte').get('0'))
    var.get('fpByte').put('58', var.get('endByte').get('40'))
    var.get('fpByte').put('59', var.get('endByte').get('8'))
    var.get('fpByte').put('60', var.get('endByte').get('48'))
    var.get('fpByte').put('61', var.get('endByte').get('16'))
    var.get('fpByte').put('62', var.get('endByte').get('56'))
    var.get('fpByte').put('63', var.get('endByte').get('24'))
    return var.get('fpByte')


PyJsHoisted_finallyPermute_.func_name = 'finallyPermute'
var.put('finallyPermute', PyJsHoisted_finallyPermute_)


@Js
def PyJsHoisted_getBoxBinary_(i, this, arguments, var=var):
    var = Scope({'i': i, 'this': this, 'arguments': arguments}, var)
    var.registers(['i', 'binary'])
    var.put('binary', Js(''))
    while 1:
        SWITCHED = False
        CONDITION = (var.get('i'))
        if SWITCHED or PyJsStrictEq(CONDITION, Js(0.0)):
            SWITCHED = True
            var.put('binary', Js('0000'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js(1.0)):
            SWITCHED = True
            var.put('binary', Js('0001'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js(2.0)):
            SWITCHED = True
            var.put('binary', Js('0010'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js(3.0)):
            SWITCHED = True
            var.put('binary', Js('0011'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js(4.0)):
            SWITCHED = True
            var.put('binary', Js('0100'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js(5.0)):
            SWITCHED = True
            var.put('binary', Js('0101'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js(6.0)):
            SWITCHED = True
            var.put('binary', Js('0110'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js(7.0)):
            SWITCHED = True
            var.put('binary', Js('0111'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js(8.0)):
            SWITCHED = True
            var.put('binary', Js('1000'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js(9.0)):
            SWITCHED = True
            var.put('binary', Js('1001'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js(10.0)):
            SWITCHED = True
            var.put('binary', Js('1010'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js(11.0)):
            SWITCHED = True
            var.put('binary', Js('1011'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js(12.0)):
            SWITCHED = True
            var.put('binary', Js('1100'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js(13.0)):
            SWITCHED = True
            var.put('binary', Js('1101'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js(14.0)):
            SWITCHED = True
            var.put('binary', Js('1110'))
            break
        if SWITCHED or PyJsStrictEq(CONDITION, Js(15.0)):
            SWITCHED = True
            var.put('binary', Js('1111'))
            break
        SWITCHED = True
        break
    return var.get('binary')


PyJsHoisted_getBoxBinary_.func_name = 'getBoxBinary'
var.put('getBoxBinary', PyJsHoisted_getBoxBinary_)


@Js
def PyJsHoisted_generateKeys_(keyByte, this, arguments, var=var):
    var = Scope({'keyByte': keyByte, 'this': this, 'arguments': arguments}, var)
    var.registers(['i', 'keyByte', 'tempRight', 'tempKey', 'keys', 'tempLeft', 'loop', 'key'])
    var.put('key', var.get('Array').create(Js(56.0)))
    var.put('keys', var.get('Array').create())
    var.get('keys').put('0', var.get('Array').create())
    var.get('keys').put('1', var.get('Array').create())
    var.get('keys').put('2', var.get('Array').create())
    var.get('keys').put('3', var.get('Array').create())
    var.get('keys').put('4', var.get('Array').create())
    var.get('keys').put('5', var.get('Array').create())
    var.get('keys').put('6', var.get('Array').create())
    var.get('keys').put('7', var.get('Array').create())
    var.get('keys').put('8', var.get('Array').create())
    var.get('keys').put('9', var.get('Array').create())
    var.get('keys').put('10', var.get('Array').create())
    var.get('keys').put('11', var.get('Array').create())
    var.get('keys').put('12', var.get('Array').create())
    var.get('keys').put('13', var.get('Array').create())
    var.get('keys').put('14', var.get('Array').create())
    var.get('keys').put('15', var.get('Array').create())
    var.put('loop',
            Js([Js(1.0), Js(1.0), Js(2.0), Js(2.0), Js(2.0), Js(2.0), Js(2.0), Js(2.0), Js(1.0), Js(2.0), Js(2.0),
                Js(2.0), Js(2.0), Js(2.0), Js(2.0), Js(1.0)]))
    # for JS loop
    var.put('i', Js(0.0))
    while (var.get('i') < Js(7.0)):
        # for JS loop
        PyJsComma(var.put('j', Js(0.0)), var.put('k', Js(7.0)))
        while (var.get('j') < Js(8.0)):
            var.get('key').put(((var.get('i') * Js(8.0)) + var.get('j')),
                               var.get('keyByte').get(((Js(8.0) * var.get('k')) + var.get('i'))))
            # update
            PyJsComma((var.put('j', Js(var.get('j').to_number()) + Js(1)) - Js(1)),
                      (var.put('k', Js(var.get('k').to_number()) - Js(1)) + Js(1)))
        # update
        (var.put('i', Js(var.get('i').to_number()) + Js(1)) - Js(1))
    var.put('i', Js(0.0))
    # for JS loop
    var.put('i', Js(0.0))
    while (var.get('i') < Js(16.0)):
        var.put('tempLeft', Js(0.0))
        var.put('tempRight', Js(0.0))
        # for JS loop
        var.put('j', Js(0.0))
        while (var.get('j') < var.get('loop').get(var.get('i'))):
            var.put('tempLeft', var.get('key').get('0'))
            var.put('tempRight', var.get('key').get('28'))
            # for JS loop
            var.put('k', Js(0.0))
            while (var.get('k') < Js(27.0)):
                var.get('key').put(var.get('k'), var.get('key').get((var.get('k') + Js(1.0))))
                var.get('key').put((Js(28.0) + var.get('k')), var.get('key').get((Js(29.0) + var.get('k'))))
                # update
                (var.put('k', Js(var.get('k').to_number()) + Js(1)) - Js(1))
            var.get('key').put('27', var.get('tempLeft'))
            var.get('key').put('55', var.get('tempRight'))
            # update
            (var.put('j', Js(var.get('j').to_number()) + Js(1)) - Js(1))
        var.put('tempKey', var.get('Array').create(Js(48.0)))
        var.get('tempKey').put('0', var.get('key').get('13'))
        var.get('tempKey').put('1', var.get('key').get('16'))
        var.get('tempKey').put('2', var.get('key').get('10'))
        var.get('tempKey').put('3', var.get('key').get('23'))
        var.get('tempKey').put('4', var.get('key').get('0'))
        var.get('tempKey').put('5', var.get('key').get('4'))
        var.get('tempKey').put('6', var.get('key').get('2'))
        var.get('tempKey').put('7', var.get('key').get('27'))
        var.get('tempKey').put('8', var.get('key').get('14'))
        var.get('tempKey').put('9', var.get('key').get('5'))
        var.get('tempKey').put('10', var.get('key').get('20'))
        var.get('tempKey').put('11', var.get('key').get('9'))
        var.get('tempKey').put('12', var.get('key').get('22'))
        var.get('tempKey').put('13', var.get('key').get('18'))
        var.get('tempKey').put('14', var.get('key').get('11'))
        var.get('tempKey').put('15', var.get('key').get('3'))
        var.get('tempKey').put('16', var.get('key').get('25'))
        var.get('tempKey').put('17', var.get('key').get('7'))
        var.get('tempKey').put('18', var.get('key').get('15'))
        var.get('tempKey').put('19', var.get('key').get('6'))
        var.get('tempKey').put('20', var.get('key').get('26'))
        var.get('tempKey').put('21', var.get('key').get('19'))
        var.get('tempKey').put('22', var.get('key').get('12'))
        var.get('tempKey').put('23', var.get('key').get('1'))
        var.get('tempKey').put('24', var.get('key').get('40'))
        var.get('tempKey').put('25', var.get('key').get('51'))
        var.get('tempKey').put('26', var.get('key').get('30'))
        var.get('tempKey').put('27', var.get('key').get('36'))
        var.get('tempKey').put('28', var.get('key').get('46'))
        var.get('tempKey').put('29', var.get('key').get('54'))
        var.get('tempKey').put('30', var.get('key').get('29'))
        var.get('tempKey').put('31', var.get('key').get('39'))
        var.get('tempKey').put('32', var.get('key').get('50'))
        var.get('tempKey').put('33', var.get('key').get('44'))
        var.get('tempKey').put('34', var.get('key').get('32'))
        var.get('tempKey').put('35', var.get('key').get('47'))
        var.get('tempKey').put('36', var.get('key').get('43'))
        var.get('tempKey').put('37', var.get('key').get('48'))
        var.get('tempKey').put('38', var.get('key').get('38'))
        var.get('tempKey').put('39', var.get('key').get('55'))
        var.get('tempKey').put('40', var.get('key').get('33'))
        var.get('tempKey').put('41', var.get('key').get('52'))
        var.get('tempKey').put('42', var.get('key').get('45'))
        var.get('tempKey').put('43', var.get('key').get('41'))
        var.get('tempKey').put('44', var.get('key').get('49'))
        var.get('tempKey').put('45', var.get('key').get('35'))
        var.get('tempKey').put('46', var.get('key').get('28'))
        var.get('tempKey').put('47', var.get('key').get('31'))
        while 1:
            SWITCHED = False
            CONDITION = (var.get('i'))
            if SWITCHED or PyJsStrictEq(CONDITION, Js(0.0)):
                SWITCHED = True
                # for JS loop
                var.put('m', Js(0.0))
                while (var.get('m') < Js(48.0)):
                    var.get('keys').get('0').put(var.get('m'), var.get('tempKey').get(var.get('m')))
                    # update
                    (var.put('m', Js(var.get('m').to_number()) + Js(1)) - Js(1))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(1.0)):
                SWITCHED = True
                # for JS loop
                var.put('m', Js(0.0))
                while (var.get('m') < Js(48.0)):
                    var.get('keys').get('1').put(var.get('m'), var.get('tempKey').get(var.get('m')))
                    # update
                    (var.put('m', Js(var.get('m').to_number()) + Js(1)) - Js(1))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(2.0)):
                SWITCHED = True
                # for JS loop
                var.put('m', Js(0.0))
                while (var.get('m') < Js(48.0)):
                    var.get('keys').get('2').put(var.get('m'), var.get('tempKey').get(var.get('m')))
                    # update
                    (var.put('m', Js(var.get('m').to_number()) + Js(1)) - Js(1))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(3.0)):
                SWITCHED = True
                # for JS loop
                var.put('m', Js(0.0))
                while (var.get('m') < Js(48.0)):
                    var.get('keys').get('3').put(var.get('m'), var.get('tempKey').get(var.get('m')))
                    # update
                    (var.put('m', Js(var.get('m').to_number()) + Js(1)) - Js(1))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(4.0)):
                SWITCHED = True
                # for JS loop
                var.put('m', Js(0.0))
                while (var.get('m') < Js(48.0)):
                    var.get('keys').get('4').put(var.get('m'), var.get('tempKey').get(var.get('m')))
                    # update
                    (var.put('m', Js(var.get('m').to_number()) + Js(1)) - Js(1))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(5.0)):
                SWITCHED = True
                # for JS loop
                var.put('m', Js(0.0))
                while (var.get('m') < Js(48.0)):
                    var.get('keys').get('5').put(var.get('m'), var.get('tempKey').get(var.get('m')))
                    # update
                    (var.put('m', Js(var.get('m').to_number()) + Js(1)) - Js(1))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(6.0)):
                SWITCHED = True
                # for JS loop
                var.put('m', Js(0.0))
                while (var.get('m') < Js(48.0)):
                    var.get('keys').get('6').put(var.get('m'), var.get('tempKey').get(var.get('m')))
                    # update
                    (var.put('m', Js(var.get('m').to_number()) + Js(1)) - Js(1))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(7.0)):
                SWITCHED = True
                # for JS loop
                var.put('m', Js(0.0))
                while (var.get('m') < Js(48.0)):
                    var.get('keys').get('7').put(var.get('m'), var.get('tempKey').get(var.get('m')))
                    # update
                    (var.put('m', Js(var.get('m').to_number()) + Js(1)) - Js(1))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(8.0)):
                SWITCHED = True
                # for JS loop
                var.put('m', Js(0.0))
                while (var.get('m') < Js(48.0)):
                    var.get('keys').get('8').put(var.get('m'), var.get('tempKey').get(var.get('m')))
                    # update
                    (var.put('m', Js(var.get('m').to_number()) + Js(1)) - Js(1))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(9.0)):
                SWITCHED = True
                # for JS loop
                var.put('m', Js(0.0))
                while (var.get('m') < Js(48.0)):
                    var.get('keys').get('9').put(var.get('m'), var.get('tempKey').get(var.get('m')))
                    # update
                    (var.put('m', Js(var.get('m').to_number()) + Js(1)) - Js(1))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(10.0)):
                SWITCHED = True
                # for JS loop
                var.put('m', Js(0.0))
                while (var.get('m') < Js(48.0)):
                    var.get('keys').get('10').put(var.get('m'), var.get('tempKey').get(var.get('m')))
                    # update
                    (var.put('m', Js(var.get('m').to_number()) + Js(1)) - Js(1))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(11.0)):
                SWITCHED = True
                # for JS loop
                var.put('m', Js(0.0))
                while (var.get('m') < Js(48.0)):
                    var.get('keys').get('11').put(var.get('m'), var.get('tempKey').get(var.get('m')))
                    # update
                    (var.put('m', Js(var.get('m').to_number()) + Js(1)) - Js(1))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(12.0)):
                SWITCHED = True
                # for JS loop
                var.put('m', Js(0.0))
                while (var.get('m') < Js(48.0)):
                    var.get('keys').get('12').put(var.get('m'), var.get('tempKey').get(var.get('m')))
                    # update
                    (var.put('m', Js(var.get('m').to_number()) + Js(1)) - Js(1))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(13.0)):
                SWITCHED = True
                # for JS loop
                var.put('m', Js(0.0))
                while (var.get('m') < Js(48.0)):
                    var.get('keys').get('13').put(var.get('m'), var.get('tempKey').get(var.get('m')))
                    # update
                    (var.put('m', Js(var.get('m').to_number()) + Js(1)) - Js(1))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(14.0)):
                SWITCHED = True
                # for JS loop
                var.put('m', Js(0.0))
                while (var.get('m') < Js(48.0)):
                    var.get('keys').get('14').put(var.get('m'), var.get('tempKey').get(var.get('m')))
                    # update
                    (var.put('m', Js(var.get('m').to_number()) + Js(1)) - Js(1))
                break
            if SWITCHED or PyJsStrictEq(CONDITION, Js(15.0)):
                SWITCHED = True
                # for JS loop
                var.put('m', Js(0.0))
                while (var.get('m') < Js(48.0)):
                    var.get('keys').get('15').put(var.get('m'), var.get('tempKey').get(var.get('m')))
                    # update
                    (var.put('m', Js(var.get('m').to_number()) + Js(1)) - Js(1))
                break
            SWITCHED = True
            break
        # update
        (var.put('i', Js(var.get('i').to_number()) + Js(1)) - Js(1))
    return var.get('keys')


PyJsHoisted_generateKeys_.func_name = 'generateKeys'
var.put('generateKeys', PyJsHoisted_generateKeys_)


def get_des_key(username: str, word: str, csrf_token: str) -> str:
    result = PyJsHoisted_strEnc_(username.strip() + word.strip() + csrf_token, "1", "2", "3")
    return str(result).strip("'")
