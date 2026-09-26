"""
                   ModelExecutor
                        │
                        ▼
                   ModelAdapter
              /          |          \
             /           |           \
     OpenAIResponses  Anthropic      Edge
          │              │            │
          ▼              ▼            ▼
       OpenAI        Anthropic     EdgeGateway
                                      │
                              ┌───────┴────────┐
                              ▼                ▼
                         gRPC session     WS session
                              │                │
                         DIOS Bridge        Browser
"""
