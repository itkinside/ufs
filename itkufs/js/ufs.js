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
Element.observe(window, 'load', Transaction.init);
