# SPDX-FileCopyrightText: 2025 chatvote
#
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

from enum import StrEnum
from pydantic import BaseModel, Field


class RAG(BaseModel):
    """RAG chain output."""

    chat_answer: str = Field(
        description="Your short answer to the user's question in Markdown format with formatting and paragraphs."
    )
    chat_title: str = Field(
        description="The short chat title in plain text. It should describe the chat concisely in 3-5 words."
    )


class QuickReplyGenerator(BaseModel):
    """Quick reply generator output."""

    quick_replies: list[str] = Field(
        description="List of three quick replies as strings."
    )


class PartyID(StrEnum):
    """Party/list identifiers for French municipal elections."""

    # These IDs will be defined dynamically based on the municipality
    # ChatVote assistant has a special ID for general questions
    ASSISTANT = "chat-vote"


class PartyListGenerator(BaseModel):
    """Party list generator output."""

    party_id_list: list[PartyID] = Field(
        description="List of party/list IDs from which the user wants to get a response."
    )


class QuestionTypeClassifier(BaseModel):
    """Question type classifier output."""

    non_party_specific_question: str = Field(
        description="The user's question, reformulated as if addressed directly to a party/list."
    )
    is_comparing_question: bool = Field(
        description="True if it's an explicit comparison question, False otherwise."
    )


class ChatSummaryGenerator(BaseModel):
    """Chat summary generator output."""

    chat_summary: str = Field(
        description="The main guiding questions that the parties/lists have answered."
    )


class GroupChatTitleQuickReplyGenerator(BaseModel):
    """Title and quick reply generator output."""

    chat_title: str = Field(
        description="A short title that describes the chat concisely in 3-5 words."
    )
    quick_replies: list[str] = Field(
        description="List of three quick replies as strings."
    )


class RerankingOutput(BaseModel):
    """Reranking model output."""

    reranked_doc_indices: list[int] = Field(
        description="List of document indices sorted by decreasing usefulness."
    )
