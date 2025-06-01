
# MIT License
#
# Copyright (c) 2023 Your Organization Name
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
This module initializes an agent for handling banking-related information using the LangChain library.
It sets up tools for different actions such as triggering fraud alerts, analyzing rate changes,
forwarding to risk team, and monitoring specific individuals or entities of interest.

DISCLAIMER: This code is for educational and demonstration purposes only. It deals with sensitive
financial topics and should not be used in real-world scenarios without proper authorization,
expert oversight, and compliance with relevant financial regulations.
"""

import os
from langchain.agents import initialize_agent, Tool
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_types import AgentType
from tools.tools_banking import trigger_fraud_alert, analyze_rate_change, forward_to_risk_team, forward_to_monitoring_team

# Initialize the language model
# The model name and temperature can be configured via environment variables
llm = ChatOpenAI(
    model_name=os.getenv("LLM_MODEL_NAME", "gpt-4"),
    temperature=float(os.getenv("LLM_TEMPERATURE", "0"))
)

tools = [
    Tool.from_function(
        func=lambda q: trigger_fraud_alert(q),
        name="trigger_fraud_alert",
        description="Use this to raise alerts about banking frauds or scams"
    ),
    Tool.from_function(
        func=lambda q: analyze_rate_change(q),
        name="analyze_rate_change",
        description="Use this to analyze interest rate updates or monetary policy changes"
    ),
    Tool.from_function(
        func=lambda q: forward_to_risk_team(q),
        name="forward_to_risk_team",
        description="Use this to escalate serious banking risks to the risk management team"
    ),
    Tool.from_function(
        func=lambda q: forward_to_monitoring_team(q),
        name="forward_to_monitoring_team",
        description="Use this to notify if the news is related to specific individuals or entities of interest"
    )
]

banking_agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)
