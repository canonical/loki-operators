output "app_name" {
  value = juju_application.loki_coordinator.name
}

output "provides" {
  value = {
    loki_cluster = "loki-cluster"
  }
}

output "requires" {
  value = {}
}
