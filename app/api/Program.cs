using HomebrewApp.Data;
using HomebrewApp.Features.Health;

using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

var conn = builder.Configuration.GetConnectionString("App")
           ?? throw new InvalidOperationException(
               "Connection string 'ConnectionStrings:App' is not set. " +
               "In development, store it in the API's user secrets; see app/README.md, \"Run the API\".");

// Add services to the container.
// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();
builder.Services.AddDbContext<AppDbContext>(options =>
{
    options.UseNpgsql(conn);
    options.UseQueryTrackingBehavior(QueryTrackingBehavior.NoTracking);
});

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.MapHealthEndpoint();

app.Run();
