# Export Delete Tree
<!-- sax:version 0.0.4 -->


Export all the records that belong selected queryset using any registered Serializer.

This action is the counterpart of [[export_as_fixture]], where it dumps the queryset and it's ForeignKeys,
[[export_delete_tree]] all the records that belong to the entries of the  selected queryset.
see `export_as_fixture`_ for details


|                     ||
|---------------------|---------------------------------------------------------------------------------------|
 **use natural key**  | If true use natural keys.
 **dump on screen**   | Dump on screen instead to show ``Save as`` popup
 **indent**           | Indentation value
 **serializer**       | Serializer to use. (see :ref:`Serialization formats <django:serialization-formats>`)
 **add_foreign_keys** | If checked export dependent objects too.


**Screenshot**

![img_export_delete_tree](_static/export_delete_tree.png)
