# IAM files

The sample role is intentionally permissionless. The application asks the AWS SDK to verify that EKS Pod Identity supplied a credential provider, but it does not call AWS service APIs. This demonstrates credential delivery without granting unnecessary AWS permissions.

The trust policy template limits assumption to the named account and EKS cluster. `scripts/create-identity-role.sh` fills in those values and creates or updates the trust policy. If you later add an AWS API call to the application, attach a separate policy scoped to that exact action and resource; do not attach administrator access.
