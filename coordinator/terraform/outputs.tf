output "app_name" {
  value = juju_application.loki_coordinator.name
}

output "requires" {
  value = {
    loki_cluster = "loki-cluster"
  }
}
