# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Group'
        db.create_table('accounting_group', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('warn_limit', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('block_limit', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('logo', self.gf('django.db.models.fields.files.ImageField')(max_length=100, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
        ))
        db.send_create_signal('accounting', ['Group'])

        # Adding M2M table for field admins on 'Group'
        db.create_table('accounting_group_admins', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm['accounting.group'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('accounting_group_admins', ['group_id', 'user_id'])

        # Adding model 'Account'
        db.create_table('accounting_account', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('short_name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounting.Group'])),
            ('type', self.gf('django.db.models.fields.CharField')(default='Li', max_length=2)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('ignore_block_limit', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('blocked', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('group_account', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('accounting', ['Account'])

        # Adding unique constraint on 'Account', fields ['slug', 'group']
        db.create_unique('accounting_account', ['slug', 'group_id'])

        # Adding unique constraint on 'Account', fields ['owner', 'group']
        db.create_unique('accounting_account', ['owner_id', 'group_id'])

        # Adding model 'RoleAccount'
        db.create_table('accounting_roleaccount', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounting.Group'])),
            ('role', self.gf('django.db.models.fields.CharField')(max_length=4)),
            ('account', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounting.Account'])),
        ))
        db.send_create_signal('accounting', ['RoleAccount'])

        # Adding model 'Settlement'
        db.create_table('accounting_settlement', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounting.Group'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('closed', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('accounting', ['Settlement'])

        # Adding model 'Transaction'
        db.create_table('accounting_transaction', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='real_transaction_set', to=orm['accounting.Group'])),
            ('settlement', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounting.Settlement'], null=True, blank=True)),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=3, blank=True)),
        ))
        db.send_create_signal('accounting', ['Transaction'])

        # Adding model 'TransactionLog'
        db.create_table('accounting_transactionlog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('transaction', self.gf('django.db.models.fields.related.ForeignKey')(related_name='log_set', to=orm['accounting.Transaction'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
        ))
        db.send_create_signal('accounting', ['TransactionLog'])

        # Adding model 'TransactionEntry'
        db.create_table('accounting_transactionentry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('transaction', self.gf('django.db.models.fields.related.ForeignKey')(related_name='entry_set', to=orm['accounting.Transaction'])),
            ('account', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounting.Account'])),
            ('debit', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=10, decimal_places=2)),
            ('credit', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=10, decimal_places=2)),
        ))
        db.send_create_signal('accounting', ['TransactionEntry'])

        # Adding unique constraint on 'TransactionEntry', fields ['transaction', 'account']
        db.create_unique('accounting_transactionentry', ['transaction_id', 'account_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'TransactionEntry', fields ['transaction', 'account']
        db.delete_unique('accounting_transactionentry', ['transaction_id', 'account_id'])

        # Removing unique constraint on 'Account', fields ['owner', 'group']
        db.delete_unique('accounting_account', ['owner_id', 'group_id'])

        # Removing unique constraint on 'Account', fields ['slug', 'group']
        db.delete_unique('accounting_account', ['slug', 'group_id'])

        # Deleting model 'Group'
        db.delete_table('accounting_group')

        # Removing M2M table for field admins on 'Group'
        db.delete_table('accounting_group_admins')

        # Deleting model 'Account'
        db.delete_table('accounting_account')

        # Deleting model 'RoleAccount'
        db.delete_table('accounting_roleaccount')

        # Deleting model 'Settlement'
        db.delete_table('accounting_settlement')

        # Deleting model 'Transaction'
        db.delete_table('accounting_transaction')

        # Deleting model 'TransactionLog'
        db.delete_table('accounting_transactionlog')

        # Deleting model 'TransactionEntry'
        db.delete_table('accounting_transactionentry')


    models = {
        'accounting.account': {
            'Meta': {'ordering': "('group', 'name')", 'unique_together': "(('slug', 'group'), ('owner', 'group'))", 'object_name': 'Account'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'blocked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounting.Group']"}),
            'group_account': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_block_limit': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'Li'", 'max_length': '2'})
        },
        'accounting.group': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Group'},
            'admins': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'block_limit': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'warn_limit': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'accounting.roleaccount': {
            'Meta': {'ordering': "('group', 'role')", 'object_name': 'RoleAccount'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounting.Account']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounting.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '4'})
        },
        'accounting.settlement': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Settlement'},
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounting.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'accounting.transaction': {
            'Meta': {'ordering': "('-last_modified',)", 'object_name': 'Transaction'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'real_transaction_set'", 'to': "orm['accounting.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'settlement': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounting.Settlement']", 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'})
        },
        'accounting.transactionentry': {
            'Meta': {'ordering': "('credit', 'debit')", 'unique_together': "(('transaction', 'account'),)", 'object_name': 'TransactionEntry'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounting.Account']"}),
            'credit': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '10', 'decimal_places': '2'}),
            'debit': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '10', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'transaction': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'entry_set'", 'to': "orm['accounting.Transaction']"})
        },
        'accounting.transactionlog': {
            'Meta': {'ordering': "('timestamp',)", 'object_name': 'TransactionLog'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'transaction': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'log_set'", 'to': "orm['accounting.Transaction']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['accounting']
