workspace {
    !identifiers hierarchical

    name "{{ product.name }}"

    model {
          properties {
            structurizr.groupSeparator "/"
            workspace_cmdb "{{ product.alias }}"
            architect "{{ architect_name }}"
          }

          my_system = softwareSystem mySystem {
            properties {
              "cmdb" "{{ product.alias }}"
            }
          }
    }

    views {
      properties {
            structurizr.sort created
            structurizr.tooltips true
        }

      systemContext my_system {
        include *
        autoLayout
      }
    }
}