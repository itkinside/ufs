var Transaction = {
  timeout: null,
  balance: {},
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

    var check = new Element('button', {'type': 'button'}).update('Check values');
    $$('#newtransaction button')[0].up().insert(check);

    check.observe('click', Transaction.update);

    tbody.select('.balance').each(
      function(td) {
        Transaction.balance[td.id] = Number(td.innerHTML);
      }
    );
    Transaction.update();
  },
  update: function() {
    var debit = 0;
    var credit = 0;
    var error = false;

    $$('#newtransaction tbody input').each(
      function(input) {
        var value = input.value;

        if (isNaN(value) || value < 0) {
          input.up().addClassName("error");
	  error = true;
        } else if (value != '')  {
          value = Number(value);

          if (input.id.match(/debit/)) {
            debit += value;
	  } else if (input.id.match(/credit/)) {
            credit += value;
	  }
          input.up().removeClassName('error');
        }
      }
    );

    $$('#newtransaction tbody .balance').each(
      function(td) {
        var diff = 0;
	var d_value = Number(td.next().down('input').value);
	var c_value = Number(td.next().next().down('input').value);

	if (!isNaN(d_value) && d_value > 0)
	  diff += d_value;
	if (!isNaN(c_value) && c_value > 0)
	  diff -= c_value;

        if(diff) {
          td.update((Transaction.balance[td.id]  + diff)+'*');
        } else {
          td.update(Transaction.balance[td.id]);
	}
      }
    );

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
	div.insert(new Element('span', {'style': 'vertical-align: top; font-weight: bold'}).update('Selected'));
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
