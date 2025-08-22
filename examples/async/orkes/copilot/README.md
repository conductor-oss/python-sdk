# Orkes Conductor Examples

Examples in this folder uses features that are available in the Orkes Conductor.
To run these examples, you need an account on Playground (https://play.orkes.io) or an Orkes Cloud account. 

### Setup SDK

```shell
python3 -m pip install conductor-python
```

### Add environment variables pointing to the conductor server

```shell
export CONDUCTOR_SERVER_URL=http://play.orkes.io/api
export CONDUCTOR_AUTH_KEY=YOUR_AUTH_KEY
export CONDUCTOR_AUTH_SECRET=YOUR_AUTH_SECRET
```

#### To run the examples with AI orchestration, export keys for OpenAI and Pinecone

```shell
export PINECONE_API_KEY=
export PINECONE_ENV=
export PINECONE_PROJECT=

export OPENAI_API_KEY=
```

