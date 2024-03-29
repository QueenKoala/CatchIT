import React, { useEffect, useState } from 'react';
import {
    TextInput,
    PasswordInput,
    Checkbox,
    Anchor,
    Paper,
    Title,
    Text,
    Container,
    Group,
    Button,
    Alert,
    Space
} from '@mantine/core';

import { AlertCircle } from 'tabler-icons-react';

import { useNavigate } from 'react-router-dom';

export default function Login() {

    const navigate = useNavigate();
    const [errors, setErrors] = useState<boolean>(false);
    const [email, setEmail] = useState<string>('');
    const [password, setPassword] = useState<string>('');

    const HandleLogin = () => {
        fetch('/api/auth-login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                password,
            }),
        })
            .then(res => res.json())
            .then(res => {
                if (res.status === 200) {
                    localStorage.setItem('token', `Bearer ${res.token}`);
                    navigate('/');
                }
                setErrors(true);
            })
    }

    useEffect(() => {
        if (localStorage.getItem('token')) {
            navigate('/');
        }
    }, [navigate])

    return (
        <Container size={420} my={40}>
            <Title
                align="center"
                sx={(theme) => ({ fontFamily: `Greycliff CF, ${theme.fontFamily}`, fontWeight: 900 })}
            >
                Welcome back!
            </Title>
            <Text color="dimmed" size="sm" align="center" mt={5}>
                Do not have an account yet?{' '}
                <Anchor<'a'> size="sm" onClick={() => navigate('/register')}>
                    Create account
                </Anchor>
            </Text>

            <Paper withBorder shadow="md" p={30} mt={30} radius="md">
                <form>
                <TextInput label="Email" placeholder="you@mantine.dev" required error={errors} value={email} onChange={(e) => setEmail(e.currentTarget.value)} />
                <PasswordInput label="Password" placeholder="Your password" required mt="md" error={errors} value={password} onChange={(e) => setPassword(e.currentTarget.value)} />
                <Group position="apart" mt="md">
                    <Checkbox label="Remember me" />
                    <Anchor<'a'> onClick={(event) => event.preventDefault()} size="sm">
                        Forgot password?
                    </Anchor>
                </Group>
                <Space h={20} />
                <Alert icon={<AlertCircle size={16} />} title="Error!" color="red" hidden={!errors}>
                    Email or password is incorrect. Try again
                </Alert>
                <Button fullWidth mt="xl" onClick={HandleLogin}>
                    Sign in
                </Button>
                </form>
            </Paper>
        </Container>
    );
}