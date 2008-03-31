/* var UFS = {
  init: function() {
    Menu.init();
    Checkbox.init();
    Transaction.init();
    Select.init('id_admins');
    Select.init('id_accounts');
  }
}; */

var Transaction = {
  // Add a sumrow to tables in form#createtransaction
  init: function() {
    var tbody = $$('#newtransaction tbody')[0];
    if (tbody == null) return;

    var row = new Element('tr', { 'style': 'font-weight: bold'})
    row.insert(new Element('td').update('Sum'));
    row.insert(new Element('td'));
    row.insert(new Element('td'));
    row.insert(new Element('td', { 'id': 'debit_sum', 'class': 'number'}));
    row.insert(new Element('td', { 'id': 'credit_sum', 'class': 'number'}));
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
    var inputs = $$('#newtransaction tbody input');

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
      $('debit_sum').removeClassName('ok');
      $('credit_sum').removeClassName('ok');
      $('debit_sum').addClassName('error');
      $('credit_sum').addClassName('error');
    } else {
      $('debit_sum').removeClassName('error');
      $('credit_sum').removeClassName('error');
      $('debit_sum').addClassName('ok');
      $('credit_sum').addClassName('ok');
    }

  }
};
Element.observe(window, 'load', Transaction.init);

var Multiselect = {
  init: function() {
    $$('select[multiple=multiple]').each( // Use css selector to get right nodes.
      function(selected) {
        // Create sibling select
        var available = new Element('select', {
	  'multiple': 'multiple',
	});

	var old_parent = selected.parentNode;
	var new_parent = new Element('p');

	new_parent.insert(old_parent.select('label')[0]);
	var div = new Element('div', {'style': 'float:left'});
	div.insert(new Element('span', {'style': 'vertical-align: top'}).update('Selected'));
	div.insert(selected);

	new_parent.insert(div);

	div = new Element('div', {'style': 'float: left; margin-left: 0.5em'});
	div.insert(new Element('span', {'style': 'vertical-align: top'}).update('Available'));
	div.insert(available);

	new_parent.insert(div);

        // Set the style of the selects.
	selected.setStyle({'height': '10em', 'display': 'block', 'marginBottom': '0.5em'});
	available.setStyle({'height': '10em', 'display': 'block', 'marginBottom': '0.5em'});

	old_parent.replace(new_parent);

	// Move non-selected items to available
	selected.select('option').each(
	  function(option) {
            if (!option.selected) {
	      available.insert(option);
	    }
	    option.selected = '';
	  }
	)

	// Add event handler for selected
	selected.observe('click',
	  function(e) {
	    if (e.element().nodeName == 'OPTION') {
	      available.insert(e.element());
	      e.element().selected = '';
	    }
	  }
	);
	// Add event handler for available
	available.observe('click',
	  function(e) {
	    if (e.element().nodeName == 'OPTION') {
	      selected.insert(e.element());
	      e.element().selected = '';
	    }
	  }
	);
      }
    );
    // Add global submit handler.
    document.observe('submit',
      function() {
        $$('select[multiple=multiple] option').each(
          function(option) {
    	    option.selected = 'selected';
          }
        )
      }
    );
  }
}
Element.observe(window, 'load', Multiselect.init);
