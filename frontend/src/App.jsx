import { useState } from 'react'
import { Button, Input, Card, Typography, Layout, Space, notification } from 'antd'
import { LinkIcon, CopyIcon } from 'lucide-react'
import './App.css'

const { Header, Content, Footer } = Layout
const { Title, Text } = Typography

// Use a relative URL or environment variable for the API endpoint
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [url, setUrl] = useState('')
  const [shortUrl, setShortUrl] = useState('')
  const [loading, setLoading] = useState(false)

  const shortenUrl = async () => {
    if (!url) return
    
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ target_url: url }),
      })
      
      if (!response.ok) throw new Error('Failed to shorten URL')
      
      const data = await response.json()
      setShortUrl(data.short_url)
      notification.success({
        message: 'URL Shortened',
        description: 'Your URL has been shortened successfully!',
      })
    } catch (error) {
      notification.error({
        message: 'Error',
        description: error.message,
      })
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(`http://localhost/${shortUrl}`)
    notification.info({
      message: 'Copied',
      description: 'Short URL copied to clipboard!',
    })
  }

  return (
    <Layout className="min-h-screen">
      <Header className="flex items-center">
        <Title level={3} className="text-white m-0 flex items-center">
          <LinkIcon className="mr-2" /> URL Shortener
        </Title>
      </Header>
      
      <Content className="p-6">
        <div className="max-w-2xl mx-auto">
          <Card className="shadow-md">
            <Space direction="vertical" size="large" className="w-full">
              <div>
                <Title level={4}>Shorten Your URL</Title>
                <Text type="secondary">Enter a long URL to make it shorter</Text>
              </div>
              
              <Input
                placeholder="https://example.com/very/long/url/that/needs/shortening"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                size="large"
                prefix={<LinkIcon size={18} />}
              />
              
              <Button 
                type="primary" 
                size="large" 
                onClick={shortenUrl}
                loading={loading}
                className="w-full"
              >
                Shorten URL
              </Button>
              
              {shortUrl && (
                <Card className="bg-gray-50">
                  <div className="flex justify-between items-center">
                    <Text strong>Your shortened URL:</Text>
                    <Button 
                      icon={<CopyIcon size={16} />} 
                      onClick={copyToClipboard}
                      size="small"
                    >
                      Copy
                    </Button>
                  </div>
                  <Text className="block mt-2 text-blue-500">
                    http://localhost/{shortUrl}
                  </Text>
                </Card>
              )}
            </Space>
          </Card>
        </div>
      </Content>
      
      <Footer className="text-center">
        URL Shortener ©{new Date().getFullYear()} - DevOps Learning Project
      </Footer>
    </Layout>
  )
}

export default App