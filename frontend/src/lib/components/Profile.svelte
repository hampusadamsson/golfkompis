<script lang="ts">
	import { mingolfProfile } from '$lib/auth/mingolfProfile.svelte';
	import { Avatar, AvatarImage, AvatarFallback } from '$lib/components/ui/avatar';
	import { Badge } from '$lib/components/ui/badge';
	import StarIcon from '@lucide/svelte/icons/star';

	const profile = $derived(mingolfProfile.profile);

	const initials = $derived(
		profile ? `${profile.firstName[0] ?? ''}${profile.lastName[0] ?? ''}`.toUpperCase() : ''
	);

	const genderLabel = $derived.by(() => {
		if (!profile) return '';
		if (profile.gender === 'M') return 'Man';
		if (profile.gender === 'K' || profile.gender === 'F') return 'Kvinna';
		return profile.gender;
	});
</script>

{#if profile}
	<article class="rounded-lg border bg-card p-6">
		<!-- Header -->
		<header class="flex items-center gap-4">
			<Avatar class="size-16">
				{#if profile.imageUrl}
					<AvatarImage
						src={profile.imageUrl}
						alt="{profile.firstName} {profile.lastName}"
					/>
				{/if}
				<AvatarFallback>{initials}</AvatarFallback>
			</Avatar>
			<div class="flex flex-col gap-1">
				<h2 class="text-xl font-semibold leading-tight">
					{profile.firstName}
					{profile.lastName}
				</h2>
				<Badge variant="outline" class="w-fit">{profile.golfId}</Badge>
			</div>
		</header>

		<!-- Stats -->
		<dl class="mt-6 grid grid-cols-3 divide-x rounded-md border">
			<div class="flex flex-col items-center py-3">
				<dt class="text-xs text-muted-foreground">HCP</dt>
				<dd class="text-lg font-semibold">{profile.hcp}</dd>
			</div>
			<div class="flex flex-col items-center py-3">
				<dt class="text-xs text-muted-foreground">Ålder</dt>
				<dd class="text-lg font-semibold">{profile.age}</dd>
			</div>
			<div class="flex flex-col items-center py-3">
				<dt class="text-xs text-muted-foreground">Kön</dt>
				<dd class="text-lg font-semibold">{genderLabel}</dd>
			</div>
		</dl>

		<!-- Clubs -->
		<div class="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
			<div>
				<p class="text-xs text-muted-foreground">Hemmaklubb</p>
				<p class="font-medium">{profile.homeClubName ?? '—'}</p>
				{#if profile.districtName}
					<p class="text-sm text-muted-foreground">{profile.districtName}</p>
				{/if}
			</div>
			{#if profile.memberClubs.length > 0}
				<div>
					<p class="mb-1 text-xs text-muted-foreground">Klubbar</p>
					<div class="flex flex-wrap gap-1.5">
						{#each profile.memberClubs as club (club.id)}
							<Badge variant={club.isHomeClub ? 'default' : 'outline'}>
								{#if club.isHomeClub}<StarIcon class="mr-1 size-3" />{/if}
								{club.name}
							</Badge>
						{/each}
					</div>
				</div>
			{/if}
		</div>

		<!-- Status -->
		<div class="mt-6 flex flex-wrap items-center gap-2 border-t pt-4">
			<Badge variant={profile.hasActiveMembership ? 'secondary' : 'destructive'}>
				{profile.hasActiveMembership ? 'Aktivt medlemskap' : 'Inget aktivt medlemskap'}
			</Badge>
			{#if !profile.allowedToBook}
				<Badge variant="destructive">Får ej boka</Badge>
			{/if}
			{#if profile.capped}
				<Badge variant="destructive">
					Capad{profile.hardCap ? ` (${profile.hardCap})` : ''}
				</Badge>
			{/if}
			{#if profile.isFederationSuspended}
				<Badge variant="destructive">Avstängd</Badge>
			{/if}
			{#if profile.isFederationSuspendedCompetition}
				<Badge variant="destructive">Tävlingsavstängd</Badge>
			{/if}
			{#if profile.emailAddress}
				<span class="ml-auto text-xs text-muted-foreground">{profile.emailAddress}</span>
			{/if}
		</div>
	</article>
{/if}
