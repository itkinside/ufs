var ufs = {
  init: function() {
    menu.init();
    checkbox.init();
  }
};

var checkbox = {
  init: function() {
    var forms = document.getElementsByTagName('form');

    for(i=0; i<forms.length; i++) {
      if(!forms[i].className.match(/togglecheckboxes/))
        continue;

      var button_parent = forms[i].getElementsByTagName('button')[0].parentNode;

      // Argh... IE sucks, tried using DOM but IE has a broken setAttribute :(
      button_parent.innerHTML += gettext('Checkboxes: ')
      	+ '<a href="#" onclick="checkbox.all(this)">'    + gettext('All')    + '</a> '
      	+ '<a href="#" onclick="checkbox.none(this)">'   + gettext('None')   + '</a> '
      	+ '<a href="#" onclick="checkbox.invert(this)">' + gettext('Invert') + '</a> ';
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

var menu = {
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

window.onload = ufs.init;
