<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import SearchIcon from '@lucide/svelte/icons/search';
	import CalendarCheckIcon from '@lucide/svelte/icons/calendar-check';
	import UsersIcon from '@lucide/svelte/icons/users';

	const features = [
		{
			icon: SearchIcon,
			title: 'Sök smartare',
			description:
				'Hitta lediga starttider på flera favoritbanor samtidigt — och boka direkt utan att klicka dig igenom Min Golf.'
		},
		{
			icon: CalendarCheckIcon,
			title: 'Full koll',
			description: 'Se kommande bokningar och avboka med ett klick. Allt på en sida, alltid uppdaterat.'
		},
		{
			icon: UsersIcon,
			title: 'Tillsammans',
			description: 'Se kompisars handicap och spelhistorik — golf är roligare med sällskap.'
		}
	];
</script>

<!-- Hero -->
<section class="flex flex-col items-center gap-6 px-4 py-24 text-center">
	<h1 class="max-w-2xl text-5xl font-bold tracking-tight">Smartare bokning för Min Golf</h1>

	<p class="max-w-xl text-lg text-muted-foreground">
		Golfkompis hjälper dig hitta starttider, hålla koll på dina bokningar och se kompisarnas spel
		— byggt ovanpå Min Golf.
	</p>

	<div class="flex flex-wrap justify-center gap-3">
		<Button size="lg" href="/profile">Logga in</Button>
		<Button size="lg" variant="outline" href="#features">Läs mer</Button>
	</div>

	<img
		src="/golf_logo.png"
		alt="Golfkompis maskot — grävling som spelar golf"
		class="mt-6 w-48 max-w-full sm:w-64 md:w-80"
		loading="eager"
		decoding="async"
	/>
</section>

<!-- Features -->
<section id="features" class="bg-muted/40 px-4 py-20">
	<div class="mx-auto max-w-5xl">
		<h2 class="mb-12 text-center text-3xl font-semibold tracking-tight">Vad kan Golfkompis?</h2>

		<div class="grid gap-6 sm:grid-cols-3">
			{#each features as feature (feature.title)}
				<Card>
					<CardHeader>
						<div class="mb-2 flex h-10 w-10 items-center justify-center rounded-md bg-primary/10">
							<feature.icon class="h-5 w-5 text-primary" />
						</div>
						<CardTitle>{feature.title}</CardTitle>
					</CardHeader>
					<CardContent>
						<CardDescription>{feature.description}</CardDescription>
					</CardContent>
				</Card>
			{/each}
		</div>
	</div>
</section>

<!-- CTA -->
<section class="flex flex-col items-center gap-6 px-4 py-24 text-center">
	<h2 class="max-w-xl text-3xl font-semibold tracking-tight">Redo att spela?</h2>
	<p class="max-w-md text-muted-foreground">
		Logga in med ditt Golf-ID — vi använder dina vanliga Min Golf-uppgifter.
	</p>
	<Button size="lg" href="/profile">Logga in</Button>
	<p class="text-muted-foreground text-xs">Golfkompis är inte anslutet till SGF eller Min Golf.</p>
</section>
