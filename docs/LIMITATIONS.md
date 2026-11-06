# Limitations

- The application is a simulated software demonstration and is not for clinical use. It does not diagnose, prescribe, replace local escalation policy, or provide a paging service.
- NEWS2 implementation requires qualified clinician review against the RCP chart and local policy before any clinical use. No clinical validation or prospective evaluation has been performed.
- There is no trained model deployed. Model integration tests use a temporary test fixture only. NEWS2 is the only alert-driving score.
- Synthetic scenario outcomes and metrics describe application behavior, not clinical accuracy, outcomes, or validation.
- Labs are synthetic and read-only. No HL7/FHIR interface, hospital device integration, live sensor stream, WebSocket, Redis, or patient-creation workflow is present.
- Compose is for local development/demo use only. TLS, production secrets management, backup/restore, high availability, monitoring, and an operational paging integration are not configured.
- The application stores minimal patient fields but has not undergone privacy, legal, regulatory, threat-model, or independent penetration review.
- Ward assignment is a demonstration authorization scope; deployment-specific identity, policy, operational procedures, and clinical governance are absent.
- Docker clean-clone execution could not be verified in this environment because Docker CLI access to the Desktop engine did not return a server response.
