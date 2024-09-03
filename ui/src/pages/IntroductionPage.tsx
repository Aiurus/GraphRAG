import { Box, Paper, Title, Text, List } from "@mantine/core";

export function IntroductionPage() {
  return (
    <Box p="lg">
      <Paper maw={640} mx="auto" shadow="xs" p="lg">
        <Title order={2} mb="lg">
          GraphRAG using Neo4j and LangChain
        </Title>
        <Text size="lg" mb="lg">
          This POC is designed as an end-to-end pipeline from constructing
          knowledge graphs to querying them using LLMs and various RAG
          approaches.
        </Text>

        <Text mb="lg">The sections are the following:</Text>
        <List type="ordered">
          <List.Item>
            <strong>Import database:</strong> Uses{" "}
            Retrieves data from MongoDB, effectively integrating it into the pipeline for subsequent processes.
          </List.Item>
          <List.Item>
            <strong>Write data to Neo4j:</strong> Uses{" "}
            Transforms and stores the imported data into Neo4j Graph Database, 
            facilitating structured representation in a graph format.
          </List.Item>
          <List.Item>
            <strong>Construct Knowledge Graph:</strong> Uses{" "}
            Establishes a detailed Knowledge Graph tailored for Retrieval-Augmented 
            Generation (RAG), enabling enhanced data relationships and context understanding.
          </List.Item>
          <List.Item>
            <strong>Combine Vector Search and Knowledge Graph:</strong> Uses{" "}
            Merges Vector Search capabilities with the Knowledge Graph to extract more 
            relevant and contextually enriched data, optimizing information retrieval for complex queries.
          </List.Item>
        </List>
      </Paper>
    </Box>
  );
}
