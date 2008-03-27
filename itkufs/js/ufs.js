var UFS = {
  init: function() {
    Menu.init();
    Checkbox.init();
    Transaction.init();
    Select.init('id_admins');
    Select.init('id_accounts');
  }
};

var Transaction = {
  // Add a sumrow to tables in form#createtransaction
  init: function() {
    var tbody = $$('#createtransaction tbody')[0];
    if (tbody == null) return;

    var row = new Element('tr', { 'class': 'sum'})
    row.insert(new Element('td').update('Sum'));
    row.insert(new Element('td', { 'id': 'debit_sum'}));
    row.insert(new Element('td', { 'id': 'credit_sum'}));
    tbody.insert(row);

    tbody.observe('keyup', Transaction.update);

    tbody.select('input').each(
      function(input) {
        input.observe('change', Transaction.update);
        input.observe('click', Transaction.update);
      }
    )
    Transaction.update();
  },
  update: function() {
    var inputs = $$('#createtransaction tbody input');

    var debit = 0;
    var credit = 0;
    var error = false;

    inputs.each(
      function(input) {
        var value = input.value;

        if (isNaN(value) || value < 0) {
          input.parentNode.addClassName("error");
	  error = true;
        } else {
          if (input.id.match(/debit/))
            debit += Number(input.value);
          else if (input.id.match(/credit/))
            credit += Number(input.value);
          input.parentNode.removeClassName('error');
        }
      }
    )

    $('debit_sum').update(debit);
    $('credit_sum').update(credit);

    if (debit != credit || error) {
      $('debit_sum').className  = 'error';
      $('credit_sum').className = 'error';
    } else {
      $('debit_sum').className  = 'ok';
      $('credit_sum').className = 'ok';
    }

  }
};

var Checkbox = {
  // Functions to add all, none and invert buttons to modify checkboxes in
  // forms with class togglecheckboxes
  init: function() {
    var forms = document.getElementsByTagName('form');

    for(i=0; i<forms.length; i++) {
      if(!forms[i].className.match(/togglecheckboxes/))
        continue;

      var button_parent = forms[i].getElementsByTagName('button')[0].parentNode;

      // Argh... IE sucks, tried using DOM but IE has a broken setAttribute :(
      button_parent.innerHTML += gettext('Checkboxes: ')
      	+ '<a href="#" onclick="Checkbox.all(this)">'    + gettext('All')    + '</a> '
      	+ '<a href="#" onclick="Checkbox.none(this)">'   + gettext('None')   + '</a> '
      	+ '<a href="#" onclick="Checkbox.invert(this)">' + gettext('Invert') + '</a> ';
    }
  },
  all: function(node) { checkbox.toggle(node,'all'); },
  none: function(node) { checkbox.toggle(node,'none'); },
  invert: function(node) { checkbox.toggle(node,'invert'); },
  toggle: function(node, mode) {
    if(mode == null) mode = 'all';

    while (node.nodeName != 'FORM') {
      if(node.parentNode)
        node = node.parentNode;
      else
        return false;
    }

    var inputs = node.getElementsByTagName('input');
    for (var i = 0; i < inputs.length; i++) {
      var input = inputs[i];
      if (input.type == 'checkbox') {
        if (mode == 'all')
          input.checked = 'checked';
        else if (mode == 'invert')
          input.checked = input.checked == true ? '' : 'checked';
        else if (mode == 'none')
          input.checked = '';
      }
    }
    return false;
  }
};

var Menu = {
  init: function () {
    // Fixes support for our drop-down menu in IE
    // Taken from http://www.alistapart.com/articles/dropdowns/
    if (document.all && document.getElementById) {
      var navRoot = document.getElementById("menulist");

      if (navRoot == null) return;

      for (i=0; i<navRoot.childNodes.length; i++) {
        var node = navRoot.childNodes[i];

	if(node == null) continue;

        if (node.nodeName == "LI") {
          node.onmouseover = function() {
            this.className += " over";
          }
          node.onmouseout = function() {
            this.className = this.className.replace(" over", "");
          }
        }
      }
    }
  }
};

// Select is a tweaked version of SelectFilter from django
var Select = {
  init: function(field_id) {
    var from_box = document.getElementById(field_id);
    if (from_box == null) return;
    from_box.id += '_from'; // change its ID

    // Create the TO box
    var to_box = document.createElement('select');
    to_box.id = field_id + '_to';
    to_box.setAttribute('multiple', 'multiple');
    to_box.setAttribute('size', from_box.size);

    var from_set = document.createElement('fieldset');
    var to_set   = document.createElement('fieldset');

    from_set.style.display = "inline";
    to_set.style.display = "inline";

    var available = document.createElement('legend');
    var chosen = document.createElement('legend');
    available.appendChild(document.createTextNode('Available:'));
    chosen.appendChild(document.createTextNode('Chosen:'));

    from_set.appendChild(available);
    to_set.appendChild(chosen);
    to_set.appendChild(to_box);

    from_box.parentNode.insertBefore(to_set, from_box.nextSibling);
    from_box.parentNode.replaceChild(from_set, from_box);

    from_set.appendChild(from_box);

    to_box.setAttribute('name', from_box.getAttribute('name'));
    from_box.setAttribute('name', from_box.getAttribute('name') + '_old');

    to_box.style.height = '8em';
    from_box.style.height = '8em';
    to_set.style.margin = '0 0 0 0.5em';

    // Set up the JavaScript event handlers for the select box filter interface
    addEvent(from_box, 'dblclick', function() { SelectBox.move(field_id + '_from', field_id + '_to'); });
    addEvent(to_box, 'dblclick', function() { SelectBox.move(field_id + '_to', field_id + '_from'); });
    addEvent(findForm(from_box), 'submit', function() { SelectBox.select_all(field_id + '_to'); });
    SelectBox.init(field_id + '_from');
    SelectBox.init(field_id + '_to');

    // Move selected from_box options to to_box
    SelectBox.move(field_id + '_from', field_id + '_to');
  }
};

// SelectBox is stolen directly from django, as is addEvent and findNode
var SelectBox = {
    cache: new Object(),
    init: function(id) {
        var box = document.getElementById(id);
        var node;
        SelectBox.cache[id] = new Array();
        var cache = SelectBox.cache[id];
        for (var i = 0; (node = box.options[i]); i++) {
            cache.push({value: node.value, text: node.text, displayed: 1});
        }
    },
    redisplay: function(id) {
        // Repopulate HTML select box from cache
        var box = document.getElementById(id);
        box.options.length = 0; // clear all options
        for (var i = 0, j = SelectBox.cache[id].length; i < j; i++) {
            var node = SelectBox.cache[id][i];
            if (node.displayed) {
                box.options[box.options.length] = new Option(node.text, node.value, false, false);
            }
        }
    },
    filter: function(id, text) {
        // Redisplay the HTML select box, displaying only the choices containing ALL
        // the words in text. (It's an AND search.)
        var tokens = text.toLowerCase().split(/\s+/);
        var node, token;
        for (var i = 0; (node = SelectBox.cache[id][i]); i++) {
            node.displayed = 1;
            for (var j = 0; (token = tokens[j]); j++) {
                if (node.text.toLowerCase().indexOf(token) == -1) {
                    node.displayed = 0;
                }
            }
        }
        SelectBox.redisplay(id);
    },
    delete_from_cache: function(id, value) {
        var node, delete_index = null;
        for (var i = 0; (node = SelectBox.cache[id][i]); i++) {
            if (node.value == value) {
                delete_index = i;
                break;
            }
        }
        var j = SelectBox.cache[id].length - 1;
        for (var i = delete_index; i < j; i++) {
            SelectBox.cache[id][i] = SelectBox.cache[id][i+1];
        }
        SelectBox.cache[id].length--;
    },
    add_to_cache: function(id, option) {
        SelectBox.cache[id].push({value: option.value, text: option.text, displayed: 1});
    },
    cache_contains: function(id, value) {
        // Check if an item is contained in the cache
        var node;
        for (var i = 0; (node = SelectBox.cache[id][i]); i++) {
            if (node.value == value) {
                return true;
            }
        }
        return false;
    },
    move: function(from, to) {
        var from_box = document.getElementById(from);
        var to_box = document.getElementById(to);
        var option;
        for (var i = 0; (option = from_box.options[i]); i++) {
            if (option.selected && SelectBox.cache_contains(from, option.value)) {
                SelectBox.add_to_cache(to, {value: option.value, text: option.text, displayed: 1});
                SelectBox.delete_from_cache(from, option.value);
            }
        }
        SelectBox.redisplay(from);
        SelectBox.redisplay(to);
    },
    move_all: function(from, to) {
        var from_box = document.getElementById(from);
        var to_box = document.getElementById(to);
        var option;
        for (var i = 0; (option = from_box.options[i]); i++) {
            if (SelectBox.cache_contains(from, option.value)) {
                SelectBox.add_to_cache(to, {value: option.value, text: option.text, displayed: 1});
                SelectBox.delete_from_cache(from, option.value);
            }
        }
        SelectBox.redisplay(from);
        SelectBox.redisplay(to);
    },
    sort: function(id) {
        SelectBox.cache[id].sort( function(a, b) {
            a = a.text.toLowerCase();
            b = b.text.toLowerCase();
            try {
                if (a > b) return 1;
                if (a < b) return -1;
            }
            catch (e) {
                // silently fail on IE 'unknown' exception
            }
            return 0;
        } );
    },
    select_all: function(id) {
        var box = document.getElementById(id);
        for (var i = 0; i < box.options.length; i++) {
            box.options[i].selected = 'selected';
        }
    }
};

function findForm(node) {
    // returns the node of the form containing the given node
    if (node.tagName.toLowerCase() != 'form') {
        return findForm(node.parentNode);
    }
    return node;
}

function addEvent(obj, evType, fn) {
    if (obj.addEventListener) {
        obj.addEventListener(evType, fn, false);
        return true;
    } else if (obj.attachEvent) {
        var r = obj.attachEvent("on" + evType, fn);
        return r;
    } else {
        return false;
    }
}

Element.observe(window, 'load', UFS.init);
