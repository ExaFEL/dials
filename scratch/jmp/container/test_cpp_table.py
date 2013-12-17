

from dials.framework.table import column_table
from scitbx.array_family import flex

table = column_table()
table['c1'] = flex.int(range(10))
table['c2'] = flex.double(range(20))
table['c3'] = flex.std_string(30)

print "Keys"
print table.keys()

print "Values"
print table.values()

print "Items"
print table.items()

print "Iterkeys"
for key in table.iterkeys():
  print key

print "IterValues"
for value in table.itervalues():
  print value

print "IterItems"
for key, value in table.iteritems():
  print key, value

print "IterRows"
for row in table.iterrows():
  print row

print "IndexRows"
print table[10]

print "Slice Table"
new_table = table[5:15]
print len(new_table)
for row in new_table:
  print row

print "Set Slice"
table[15:20] = new_table
for row in table:
  print row

print "c1" in table
print "c" in table

table[10] = { 'c1' : 100 }
table[11] = { 'c1' : 200, 'c3' : "Hello World" }

print table[10]
print table[11]

table = column_table([
  ("column_1", flex.int()),
  ("column_2", flex.std_string())])

print list(table.iterkeys())

table.append({ 'column_1' : 200, 'column_2' : "Hello World 1" })
table.append({ 'column_1' : 300, 'column_2' : "Hello World 2" })
table.append({ 'column_1' : 400, 'column_2' : "Hello World 3" })
table.append({ 'column_1' : 500, 'column_2' : "Hello World 4" })

for row in table.iterrows():
  print row

table.insert(2, { 'column_1' : 1000 })

for row in table.iterrows():
  print row

print "Extend"
table.extend(table)


for row in table.iterrows():
  print row

new_table = column_table([
  ("column_2", flex.int()),
  ("column_3", flex.int()),
  ("column_4", flex.std_string())])

table.update(new_table)

for row in table.iterrows():
  print row
