import { z } from "zod";
import { useForm, zodResolver } from "@mantine/form";
import {
  TextInput,
  Button,
  Group,
  NumberInput,
  Paper,
  Title,
  Text,
  Box,
  Select,
  Notification,
  rem,
  Alert,
} from "@mantine/core";
import { useMutation } from "@tanstack/react-query";
import { importArticles } from "../../api";
import { FormEvent, useState } from "react";
import { IconCheck, IconInfoCircle, IconX } from "@tabler/icons-react";

export function ImportArticles() {
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const form = useForm({});

  const mutation = useMutation({
    mutationFn: importArticles,
    onSuccess: () => {
      setSuccessMessage(`Successfully imported articles!`);
    },
    onError: () => {
      setErrorMessage("Failed to import articles.");
    },
  });

  const handleFormSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSuccessMessage("");
    setErrorMessage("");
    mutation.mutate();
  };

  const handleNotificationClose = () => {
    setSuccessMessage("");
    setErrorMessage("");
  };

  return (
    <Box p="lg">
      <Paper maw={640} mx="auto" shadow="xs" p="lg">
        <Title order={2} mb="lg">
          Knowledge Graph Construction
        </Title>
        <Alert variant="light" color="blue" icon={<IconInfoCircle />} mb="lg">
          The Database Import API facilitates the seamless transfer of data from 
          MongoDB into Neo4j. This API not only writes queries to Neo4j but also 
          constructs a comprehensive knowledge graph designed for Retrieval-Augmented 
          Generation (RAG) processes, thus enabling advanced data analytics and 
          relationship mapping.
        </Alert>
        {successMessage ? (
          <Notification
            icon={<IconCheck style={{ width: rem(20), height: rem(20) }} />}
            color="teal"
            title="Done!"
            mt="md"
            withBorder
            style={{ boxShadow: "none" }}
            onClose={handleNotificationClose}
          >
            {successMessage}
          </Notification>
        ) : (
          <>
            <form onSubmit={handleFormSubmit}>
              {errorMessage && (
                <Notification
                  icon={<IconX style={{ width: rem(20), height: rem(20) }} />}
                  withBorder
                  color="red"
                  title="Error!"
                  mt="lg"
                  style={{ boxShadow: "none" }}
                  onClose={handleNotificationClose}
                >
                  {errorMessage}
                </Notification>
              )}
              {form.errors["query.tag"] && (
                <Notification
                  icon={<IconX style={{ width: rem(20), height: rem(20) }} />}
                  withBorder
                  color="red"
                  title="Error!"
                  mt="lg"
                  style={{ boxShadow: "none" }}
                  withCloseButton={false}
                >
                  {form.errors["query.tag"]}
                </Notification>
              )}
              <Group mt="lg">
                <Button color="teal" loading={mutation.isPending} type="submit">
                  Import
                </Button>
              </Group>
            </form>
          </>
        )}
      </Paper>
    </Box>
  );
}
