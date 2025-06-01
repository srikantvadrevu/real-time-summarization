
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
This module initializes an agent for handling terrorism-related information using the LangChain library.
It sets up tools for different actions such as triggering emergency alerts, forwarding to security operations,
and flagging for government review.

DISCLAIMER: This code is for educational and demonstration purposes only. It deals with sensitive topics
and should not be used in real-world scenarios without proper authorization and expert oversight.
"""

import os
from langchain.agents import initialize_agent, Tool
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_types import AgentType
from tools.tools_terrorism import (
    trigger_emergency_alert,
    forward_to_security_ops,
    flag_for_gov_review
)

# Initialize the language model
# The model name and temperature can be configured via environment variables
llm = ChatOpenAI(
    model_name=os.getenv("LLM_MODEL_NAME", "gpt-4"),
    temperature=float(os.getenv("LLM_TEMPERATURE", "0"))
)

tools = [
    Tool.from_function(
        func=lambda q: trigger_emergency_alert(q),
        name="trigger_emergency_alert",
        description="Use for articles describing active threats, bombings, or terrorist attacks"
    ),
    Tool.from_function(
        func=lambda q: forward_to_security_ops(q),
        name="forward_to_security_ops",
        description="Use for intelligence reports or suspected terrorism activity"
    ),
    Tool.from_function(
        func=lambda q: flag_for_gov_review(q),
        name="flag_for_gov_review",
        description="Use when the intent is unclear or for high-risk, unconfirmed intel"
    )
]

terrorism_agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)
