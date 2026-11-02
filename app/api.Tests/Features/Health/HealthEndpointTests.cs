using System.Text.Json;
using Microsoft.AspNetCore.Mvc.Testing;

namespace HomebrewApp.Tests.Features.Health;

public class HealthEndpointTests(WebApplicationFactory<Program> factory) : IClassFixture<WebApplicationFactory<Program>>
{
    [Fact]
    public async Task HealthCheckTest()
    {
        var client = factory.CreateClient();

        var response = await client.SendAsync(new HttpRequestMessage(HttpMethod.Get, "/api/health"));
        
        Assert.True(response.IsSuccessStatusCode);
        
        using var document = await JsonDocument.ParseAsync(await response.Content.ReadAsStreamAsync());
        var root = document.RootElement;
    
        // This throws an exception if 'Status' (case-sensitive) doesn't exist
        var statusProperty = root.GetProperty("status"); 
        
        Assert.Equal("ok", statusProperty.GetString());    }
}
